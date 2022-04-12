'''
系统部门信息管理
'''
from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for, jsonify, session
from flask_login import login_required, current_user
from pm.models import BizDepartment, BizCompany, BizEnterprise
from pm.plugins import db
from pm.forms.biz.organization.department import DepartmentSearchForm, DepartmentForm
from pm.decorators import log_record
from pm.views.biz.organization.company import get_enterprises
import uuid, time
from datetime import datetime
bp_department = Blueprint('department', __name__)
@bp_department.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查询部门清单')
def index():
    form = DepartmentSearchForm()
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            code = session['department_view_search_code'] if session['department_view_search_code'] else ''  # 组织代码
            name = session['department_view_search_name'] if session['department_view_search_name'] else ''  # 组织名称
        except KeyError:
            code = ''
            name = ''
        form.code.data = code
        form.name.data = name
    if request.method == 'POST':
        page = 1
        code = form.code.data
        name = form.name.data
        session['department_view_search_code'] = code.strip()
        session['department_view_search_name'] = name.strip()
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    pagination = BizDepartment.query.filter(BizDepartment.code.like('%' + code.strip() + '%'), BizDepartment.name.like('%' + name.strip() + '%')).order_by( BizDepartment.code).paginate(page, per_page)
    '''
    if current_user.is_admin:
        pagination = BizDepartment.query.filter(BizDepartment.code.like('%'+code.strip()+'%'), BizDepartment.name.like('%'+name.strip()+'%')).order_by(BizDepartment.code).paginate(page, per_page)
    else:
        pagination = BizDepartment.query.with_parent(current_user.company).filter(BizDepartment.code.like('%' + code.strip() + '%'), BizDepartment.name.like('%' + name.strip() + '%')).order_by(BizDepartment.code).paginate(page, per_page)
    '''
    departments = pagination.items
    return render_template('biz/organization/department/index.html', pagination=pagination, departments=departments, form=form)
@bp_department.route('/add', methods=['GET', 'POST'])
@login_required
@log_record('新增部门信息')
def add():
    print('Request method is : ', request.method)
    form = DepartmentForm()
    # 无论是GET还是POST,事业处信息都要获取
    enterprises, enterprise_options = get_enterprises()
    form.enterprise.choices = enterprise_options
    if request.method == 'GET':
        form.do_save.data = 0
        current_enterprise = enterprises[0] if current_user.is_admin else current_user.company.enterprise
        companies, company_options = get_companies(current_enterprise)
        current_company = companies[0]
    if request.method == 'POST':
        '''
            通过select change事件提交表单实现事业处、法人、上级部门的联动
        '''
        print('Current enterprise id is : ', form.enterprise.data)
        enterprise_id = form.enterprise.data if form.enterprise.data else current_user.company.enterprise.id
        current_enterprise = BizEnterprise.query.get(enterprise_id)
        companies, company_options = get_companies(current_enterprise)
        company_id = form.company.data if form.company.data else current_user.company.id
        company = BizCompany.query.get(company_id)
        current_company = company if company.enterprise.id == current_enterprise.id else companies[0]
        if form.do_save.data == '1':
            print('执行check...')
            code = form.code.data.strip()
            name = form.name.data.strip()
            check_ok = True
            if code:
                if BizDepartment.query.with_parent(current_company).filter_by(code=form.code.data.lower()).first():
                    check_ok = False
                    flash('部门代码已存在!')
            else:
                check_ok = False
                flash('部门代码为空!')
            if name:
                if BizDepartment.query.with_parent(current_company).filter_by(name=form.name.data).first():
                    check_ok = False
                    flash('部门名称已存在!')
            else:
                check_ok = False
                flash('部门名称为空!')
            if check_ok:
                print('数据库保存。。。')
                department = BizDepartment(
                    id=uuid.uuid4().hex,
                    code=form.code.data.lower(),
                    name=form.name.data,
                    company_id=form.company.data if current_user.is_admin else current_user.company.id,
                    create_id=current_user.id
                )
                db.session.add(department)
                db.session.commit()
                has_parent = form.has_parent.data
                if has_parent and form.parent.data is not None:
                    department.set_parent_department(BizDepartment.query.get(form.parent.data))
                flash('部门信息添加成功！')
                return redirect(url_for('.index'))
    form.company.choices = company_options
    departments = BizDepartment.query.with_parent(current_company).order_by(BizDepartment.code).all()
    department_list = []
    for department in departments:
        department_list.append((department.id, department.name))
    form.parent.choices = department_list
    return render_template('biz/organization/department/add.html', form=form)
@bp_department.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@log_record('修改部门信息')
def edit(id):
    form = DepartmentForm()
    edit_department = BizDepartment.query.get_or_404(id)
    '''
        设置上级部门下拉列表
        注:上级部门下拉列表需剔除当前部门及子部门
    '''
    self_and_children = [edit_department.id]
    get_child_departments(edit_department, self_and_children)  # 递归获取子部门及子子部门
    print('Self and child department ids : ', self_and_children)
    departments = BizDepartment.query.with_parent(edit_department.company).order_by(BizDepartment.code).all()
    department_list = []
    for department in departments:
        if department.id not in self_and_children:
            department_list.append((department.id, department.name))
    form.parent.choices = department_list
    '''enterprises, enterprise_options = get_enterprises()
    form.enterprise.choices = enterprise_options
    form.company.choices = get_companies(edit_department.company.enterprise)[1]
    '''
    print('Edit department request method : ', request.method)
    if request.method == 'GET':
        form.id.data = edit_department.id
        form.code.data = edit_department.code
        form.name.data = edit_department.name
        # form.company.data = edit_department.company.id
        # form.enterprise.data = edit_department.company.enterprise.id
        form.parent.data = edit_department.get_parent_department.id if edit_department.get_parent_department else ''
    if request.method == 'POST':
        new_code = form.code.data.strip()
        new_name = form.name.data.strip()
        check_ok = True
        if new_code:
            old_code = edit_department.code
            codes = []
            all_departments = BizDepartment.query.with_parent(edit_department.company).all()
            for department in all_departments:
                codes.append(department.code)
            # 剔除未更新前的部门代码
            codes.remove(old_code)
            # Check新的部门代码是否已经存在
            if new_code in codes:
                check_ok = False
                flash('部门代码已存在!')
        else:
            check_ok = False
            flash('部门代码为空!')
        if new_name:
            old_name = edit_department.name
            names = []
            for department in BizDepartment.query.with_parent(edit_department.company).all():
                names.append(department.name)
            # 剔除未更新前的部门名称
            names.remove(old_name)
            # Check新的部门名称是否已经存在
            if new_name in names:
                check_ok = False
                flash('部门名称已存在!')
        else:
            check_ok = False
            flash('部门名称为空!')
        if check_ok:
            edit_department.code = form.code.data
            edit_department.name = form.name.data
            # edit_department.company_id = form.company.data
            edit_department.update_id = current_user.id
            edit_department.updatetime_utc = datetime.utcfromtimestamp(time.time())
            edit_department.updatetime_loc = datetime.fromtimestamp(time.time())
            db.session.commit()
            has_parent = form.has_parent.data
            if has_parent and form.parent.data is not None:
                edit_department.set_parent_department(BizDepartment.query.get(form.parent.data))
            else:
                print('不执行上级部门更新')
            flash('部门信息更新成功！')
            return redirect(url_for('.index', id=form.id.data))
    return render_template('biz/organization/department/edit.html', form=form)
# 递归获取子部门(多级部门)
def get_child_departments(parent, children):
    child_departments = parent.get_child_department
    if child_departments:
        for child in child_departments:
            children.append(child.child_department_id)
            get_child_departments(BizDepartment.query.get(child.child_department_id), children)
    else:
        return children
@bp_department.route('/status/<id>/<int:status>', methods=['POST'])
@log_record('更改部门状态')
def status(id, status):
    department = BizDepartment.query.get_or_404(id)
    department.active = True if status == 1 else False
    department.update_id = current_user.id
    department.updatetime_utc = datetime.utcfromtimestamp(time.time())
    department.updatetime_loc = datetime.fromtimestamp(time.time())
    db.session.commit()
    return jsonify(code=1, message='状态更新成功!')
def get_companies(enterprise):
    companies = BizCompany.query.with_parent(enterprise).order_by(BizCompany.name).all()
    company_options = []
    for company in companies:
        company_options.append((company.id, company.name))
    return (companies, company_options)