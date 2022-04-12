'''
系统用户信息管理
'''
from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash, jsonify, session
from flask_login import login_required, current_user
from pm.decorators import log_record
from pm.plugins import db
from pm.models import SysUser, SysRole, BizCompany
from pm.forms.system.user import UserSearchForm, UserForm
import uuid, time
from datetime import datetime
bp_user = Blueprint('user', __name__)
@bp_user.route('/index', methods=['GET', 'POST'])
@login_required
@log_record('查看用户清单')
def index():
    form = UserSearchForm()
    if request.method == 'GET':
        page = request.args.get('page', 1, type=int)
        try:
            code = session['user_view_search_code'] if session['user_view_search_code'] else ''  # 用户代码
            name = session['user_view_search_name'] if session['user_view_search_name'] else ''  # 用户名称
        except KeyError:
            code = ''
            name = ''
        form.code.data = code
        form.name.data = name
    if request.method == 'POST':
        page = 1
        code = form.code.data.strip()
        name = form.name.data.strip()
        session['user_view_search_code'] = code
        session['user_view_search_name'] = name
    per_page = current_app.config['ITEM_COUNT_PER_PAGE']
    # 非管理员只取本法人的用户
    if current_user.is_admin:
        pagination = SysUser.query.filter(SysUser.user_id.like('%'+code+'%'),
                                          SysUser.user_name.like('%'+name+'%'),
                                          SysUser.user_id != 'admin').order_by(SysUser.user_name).paginate(page, per_page)
    else:
        pagination = SysUser.query.with_parent(current_user.company).filter(SysUser.user_id.like('%' + code + '%'),
                                          SysUser.user_name.like('%' + name + '%')).order_by(SysUser.user_name).paginate(page, per_page)
    users = pagination.items
    return render_template('system/users/index.html', form=form, pagination=pagination, users=users)
@bp_user.route('/add', methods=['GET', 'POST'])
@login_required
@log_record('新增用户')
def add():
    form = UserForm()
    roles, companies = get_user_selects()
    form.role.choices = roles
    form.company.choices = companies
    if current_user.company:
        form.company.data = current_user.company.id
    if form.validate_on_submit():
        user = SysUser(
            id=uuid.uuid4().hex,
            user_id=form.code.data.lower(),
            user_name=form.name.data,
            email=form.email.data.lower(),
            phone=form.phone.data,
            role_id=form.role.data,
            company_id=form.company.data,
            is_ad=form.is_ad.data,
            create_id=current_user.id
        )
        if not form.is_ad.data:
            user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('用户添加成功！')
        return redirect(url_for('.index'))
    return render_template('system/users/add.html', form=form)
#获取角色/部门下拉清单
def get_user_selects():
    roles = []
    companies = []
    for role in SysRole.query.filter(SysRole.name != 'Administrator', SysRole.company_id == current_user.company_id).order_by(SysRole.name).all():
        roles.append((role.id, role.name))
    for company in BizCompany.query.order_by(BizCompany.code).all():
        companies.append((company.id, company.name))
    return roles, companies
@bp_user.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
@log_record('编辑用户')
def edit(id):
    form = UserForm()
    user = SysUser.query.get_or_404(id)
    roles, companies = get_user_selects()
    form.role.choices = roles
    form.company.choices = companies
    if request.method == 'GET':
        form.id.data = user.id
        form.code.data = user.user_id
        form.name.data = user.user_name
        form.is_ad.data = user.is_ad
        form.company.data = user.company_id
        form.role.data = user.role_id
        form.email.data = user.email
        form.phone.data = user.phone
    if form.validate_on_submit():
        user.user_id = form.code.data.lower()
        user.user_name = form.name.data
        user.email = form.email.data.lower()
        user.role_id = form.role.data
        user.company_id = form.company.data
        user.is_ad = form.is_ad.data
        user.update_id = current_user.id
        user.updatetime_utc = datetime.utcfromtimestamp(time.time())
        user.updatetime_loc = datetime.fromtimestamp(time.time())
        if not form.is_ad.data and form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('用户修改成功！')
        return redirect(url_for('.index'))
    return render_template('system/users/edit.html', form=form)
@bp_user.route('/status/<id>/<int:status>', methods=['POST'])
@log_record('更改用户状态')
def status(id, status):
    user = SysUser.query.get_or_404(id)
    user.active = True if status == 1 else False
    user.update_id = current_user.id
    user.updatetime_utc = datetime.utcfromtimestamp(time.time())
    user.updatetime_loc = datetime.fromtimestamp(time.time())
    db.session.commit()
    return jsonify(code=1, message='状态更新成功!')
@bp_user.route('/reset_password/<id>', methods=['POST'])
@log_record('重置密码')
def reset_password(id):
    user = SysUser.query.get_or_404(id)
    user.set_password('Di123456')
    user.update_id = current_user.id
    user.updatetime_utc = datetime.utcfromtimestamp(time.time())
    user.updatetime_loc = datetime.fromtimestamp(time.time())
    db.session.commit()
    return jsonify(code=1, message='密码重置成功！')