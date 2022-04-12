from pm.plugins import scheduler, db
from pm.models import SysUser, SysLog, BizDepartment, BizCompany, RelDepartment, BizEmployee
import uuid, time
from datetime import datetime
from pm.infs.If_HR import get_employees, get_departments
def synchronize_hr_data_job():
    '''
    同步HR部门/雇员信息
    :return:
    '''
    # 使用上下文，否则报错
    with scheduler.app.app_context():
        app = scheduler.app
        user = SysUser.query.filter_by(user_id='admin').first()
        print('-' * 80)
        # 法人代码/ID字典
        company_map = {company.code: company.id for company in BizCompany.query.all()}
        print('开始同步部门信息')
        items = get_departments()
        for item in items:
            department = BizDepartment.query.filter_by(code=item.code).first()
            if department:
                print('Department name : ', item.name, ', type : ', type(item.name))
                department.name = item.name,
                department.company_id = company_map[item.company_code]
                department.update_id = user.id
                department.updatetime_utc = datetime.utcfromtimestamp(time.time())
                department.updatetime_loc = datetime.fromtimestamp(time.time())
            else:
                department = BizDepartment(
                    id=uuid.uuid4().hex,
                    code=item.code,
                    name=item.name,
                    company_id=company_map[item.company_code],
                    create_id=user.id
                )
                db.session.add(department)
            db.session.commit()
        print('同步部门信息完成，开始维护上级部门信息')
        # 批量删除关联关系后重新创建
        db.session.query(RelDepartment).delete()
        db.session.commit()
        # 重新创建上级部门信息
        for item in items:
            department = BizDepartment.query.filter_by(code=item.code).first()
            upper_department = BizDepartment.query.filter_by(code=item.upper_department_code).first()
            if department and upper_department:
                department.set_parent_department(upper_department)
        print('上级部门关系维护完成')
        print('开始同步雇员信息')
        # 部门代码/ID字典
        department_map = {department.code: department.id for department in BizDepartment.query.all()}
        items = get_employees()
        print('雇员数量 : ', len(items))
        count = 0
        for item in items:
            count += 1
            employee = BizEmployee.query.filter_by(code=item.code).first()
            if employee:
                print('Item(%d)执行雇员更新:职号(%s) --- ' %(count, item.code))
                employee.name = item.name
                employee.company_id = company_map[item.company_id]
                employee.department_id = department_map[item.department_code]
                employee.email = item.email
                employee.phone = item.phone
                if item[4] != '3':
                    employee.active = False
                employee.update_id = user.id
                employee.updatetime_utc = datetime.utcfromtimestamp(time.time())
                employee.updatetime_loc = datetime.fromtimestamp(time.time())
            else:
                print('Item(%d)执行雇员新增:职号(%s) --- ' %(count, item[2]))
                employee = BizEmployee(
                    id=uuid.uuid4().hex,
                    code=item.code,
                    name=item.name,
                    active=True if item.status == '3' else False,
                    company_id=company_map[item.company_id],
                    department_id=department_map[item.department_code],
                    email=item.email,
                    phone=item.phone,
                    create_id=user.id
                )
                db.session.add(employee)
            db.session.commit()
        print('雇员信息同步完成')
        print('写入日志')
        # 写入日志
        user = SysUser.query.filter_by(user_id='admin').first()
        log = SysLog(id=uuid.uuid4().hex, url='null', operation='HR数据同步成功', create_id=user.id, user_id=user.id)
        db.session.add(log)
        db.session.commit()