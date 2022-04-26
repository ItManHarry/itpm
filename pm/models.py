from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from pm.plugins import db
from datetime import datetime
import uuid
'''
通用模型
'''
class BaseModel():
    id = db.Column(db.String(32), primary_key=True)                     # 表主键ID
    active = db.Column(db.Boolean, default=True)                        # 是否使用(默认已使用)
    createtime_utc = db.Column(db.DateTime, default=datetime.utcnow)    # 创建时间(UTC标准时间)
    createtime_loc = db.Column(db.DateTime, default=datetime.now)       # 创建时间(本地时间)
    create_id = db.Column(db.String(32))                                # 创建人员
    updatetime_utc = db.Column(db.DateTime, default=datetime.utcnow)    # 更新时间(UTC标准时间)
    updatetime_loc = db.Column(db.DateTime, default=datetime.now)       # 更新时间(本地时间)
    update_id = db.Column(db.String(32))                                # 更新人员
'''
系统用户
'''
class SysUser(BaseModel, db.Model, UserMixin):
    user_id = db.Column(db.String(16), unique=True)                                         # 用户代码
    user_name = db.Column(db.String(24))                                                    # 用户姓名
    user_pwd_hash = db.Column(db.String(128))                                               # 用户密码(加密后)
    is_ad = db.Column(db.Boolean, default=False)                                            # 工厂AD
    is_admin = db.Column(db.Boolean, default=False)                                         # 是否是系统管理员(只在初始化时为True,其他均莫非False)
    email = db.Column(db.String(128))                                                       # 邮箱
    phone = db.Column(db.String(24))                                                        # 电话
    role_id = db.Column(db.String(32), db.ForeignKey('sys_role.id'))                        # 系统角色ID
    role = db.relationship('SysRole', back_populates='users')                               # 系统角色
    company_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))                  # 所属法人ID
    company = db.relationship('BizCompany', back_populates='users')                                 # 所属法人
    used_menus = db.relationship('SysMenu', secondary='rel_user_menu', back_populates='users')      # 使用过的菜单项(用于主页显示)
    logs = db.relationship('SysLog', back_populates='user')                                         # 操作日志

    def set_password(self, password):
        self.user_pwd_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.user_pwd_hash, password)
    # 已授权菜单code数据
    @property
    def menus(self):
        ms = self.role.menus
        return [menu.code for menu in ms if menu.active]
    # 用户菜单权限(返回:模块ID-菜单List字典)
    @property
    def authed_menus(self):
        module_menu = {}
        modules = self.authed_modules
        menus = self.role.menus
        menu_ids = []
        for menu in menus:
            if menu.active:
                menu_ids.append(menu.id)
        for module in modules:
            module_menu[module.id] = SysMenu.query.filter(SysMenu.module_id == module.id, SysMenu.id.in_(menu_ids)).order_by(SysMenu.order_by).all()
        return module_menu
    # 用户模块权限
    @property
    def authed_modules(self):
        '''
        获取当前用户的菜单权限
        '''
        menus = self.role.menus
        if menus:
            '''
            获取用户模块权限
            '''
            module_ids = []
            for menu in menus:
                if menu.active and menu.module_id not in module_ids:
                    module_ids.append(menu.module_id)
            '''
            重新查询并排序
            '''
            modules = SysModule.query.filter(SysModule.id.in_(module_ids)).order_by(SysModule.order_by.desc()).all()
        else:
            return []
        return modules

'''
用户菜单关联表(多对多) - 用于主页显示使用过的功能项
'''
rel_user_menu = db.Table('rel_user_menu',
    db.Column('user_id', db.String(32), db.ForeignKey('sys_user.id')),
    db.Column('menu_id', db.String(32), db.ForeignKey('sys_menu.id'))
)
'''
角色菜单关联表(多对多)
'''
rel_role_menu = db.Table('rel_role_menu',
    db.Column('role_id', db.String(32), db.ForeignKey('sys_role.id')),
    db.Column('menu_id', db.String(32), db.ForeignKey('sys_menu.id'))
)
'''
系统角色
'''
class SysRole(BaseModel, db.Model):
    name = db.Column(db.String(64), unique=True)                                            # 角色名称
    company_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))                  # 所属法人ID
    company = db.relationship('BizCompany', back_populates='roles')                         # 所属法人
    users = db.relationship('SysUser', back_populates='role')                               # 用户
    menus = db.relationship('SysMenu', secondary='rel_role_menu', back_populates='roles')   # 菜单

'''
系统模块
'''
class SysModule(BaseModel, db.Model):
    code = db.Column(db.String(12), unique=True)                # 模块代码(用以导航状态)
    name = db.Column(db.String(24), unique=True)                # 模块名称
    order_by = db.Column(db.Integer)                            # 排序
    menus = db.relationship('SysMenu', back_populates='module') # 和菜单建立一对多关联关系
'''
系统菜单
'''
class SysMenu(BaseModel, db.Model):
    code = db.Column(db.String(12), unique=True)    # 菜单代码
    name = db.Column(db.String(64))                 # 菜单名
    url = db.Column(db.String(24))                  # URL地址
    remark = db.Column(db.String(128))              # 菜单描述
    icon = db.Column(db.String(24))                 # 图标
    order_by = db.Column(db.Integer)                # 排序
    module_id = db.Column(db.String(32), db.ForeignKey('sys_module.id'))
    module = db.relationship('SysModule', back_populates='menus')
    roles = db.relationship('SysRole', secondary='rel_role_menu', back_populates='menus')
    users = db.relationship('SysUser', secondary='rel_user_menu', back_populates='used_menus')
'''
下拉字典
'''
class SysDict(BaseModel, db.Model):
    code = db.Column(db.String(24), unique=True)    # 字典代码
    name = db.Column(db.String(24), unique=True)    # 字典名称
    enums = db.relationship('SysEnum', back_populates='dictionary', cascade='all')
'''
下拉字典枚举值
'''
class SysEnum(BaseModel, db.Model):
    item = db.Column(db.String(8))                                                              # 枚举value(对应<option>标签中的value属性)
    display = db.Column(db.String(128))                                                         # 枚举view(对应<option>?</option>的显示值)
    order_by = db.Column(db.Integer)                                                            # 排序
    dict_id = db.Column(db.String(32), db.ForeignKey('sys_dict.id'))                            # 所属字典ID
    dictionary = db.relationship('SysDict', back_populates='enums')                             # 所属字典
'''
系统操作日志
'''
class SysLog(BaseModel, db.Model):
    url = db.Column(db.String(250))             # 菜单url
    operation = db.Column(db.Text)              # 操作内容
    user_id = db.Column(db.String(32), db.ForeignKey('sys_user.id'))
    user = db.relationship('SysUser', back_populates='logs')
'''
事业处信息表
'''
class BizEnterprise(BaseModel, db.Model):
    code = db.Column(db.String(10), unique=True)            # 事业处代码
    name = db.Column(db.String(128))                        # 事业处名称
    companies = db.relationship('BizCompany', back_populates='enterprise')
    # 初始化事业处
    @staticmethod
    def init_enterprises():
        enterprises = (
            ('HDI', '现代斗山'),
            ('HCE', '苏州建机'),
        )
        for item in enterprises:
            enterprise = BizEnterprise.query.filter_by(code=item[0]).first()
            if enterprise is None:
                enterprise = BizEnterprise(
                    id=uuid.uuid4().hex,
                    code=item[0],
                    name=item[1]
                )
                db.session.add(enterprise)
                db.session.commit()
'''
法人信息表
'''
class BizCompany(BaseModel, db.Model):
    code = db.Column(db.String(10))                         # 法人代码
    name = db.Column(db.String(128))                        # 法人名称
    enterprise_id = db.Column(db.String(32), db.ForeignKey('biz_enterprise.id'))
    enterprise = db.relationship('BizEnterprise', back_populates='companies')
    users = db.relationship('SysUser', back_populates='company')
    roles = db.relationship('SysRole', back_populates='company')
    departments = db.relationship('BizDepartment', back_populates='company')
    employees = db.relationship('BizEmployee', back_populates='company')
    # 初始化法人
    @staticmethod
    def init_companies():
        # 数据说明：法人代码 法人名称 事业处代码
        companies = (
            ('01920601', 'HDICC', 'HDI'),
            ('01920773', 'HDCFL', 'HDI'),
            ('01920052', 'HDISD', 'HDI'),
            ('01920000', 'HDICI', 'HDI'),
        )
        for item in companies:
            company = BizCompany.query.filter_by(code=item[0]).first()
            enterprise = BizEnterprise.query.filter_by(code=item[2]).first()
            if company is None:
                company = BizCompany(
                    id=uuid.uuid4().hex,
                    code=item[0],
                    name=item[1],
                    enterprise_id=enterprise.id if enterprise else ''
                )
                db.session.add(company)
                db.session.commit()
'''
部门层级关系
'''
class RelDepartment(BaseModel, db.Model):
    parent_department_id = db.Column(db.String(32), db.ForeignKey('biz_department.id'))
    parent_department = db.relationship('BizDepartment', foreign_keys=[parent_department_id], back_populates='parent_department', lazy='joined')    # 父部门
    child_department_id = db.Column(db.String(32), db.ForeignKey('biz_department.id'))
    child_department = db.relationship('BizDepartment', foreign_keys=[child_department_id], back_populates='child_department', lazy='joined')       # 子部门
'''
部门
'''
class BizDepartment(BaseModel, db.Model):
    code = db.Column(db.String(32))                                         # 部门代码
    name = db.Column(db.Text)                                               # 部门名称
    company_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))  # 所属法人ID
    company = db.relationship('BizCompany', back_populates='departments')   # 所属法人
    employees = db.relationship('BizEmployee', back_populates='department')
    parent_department = db.relationship('RelDepartment', foreign_keys=[RelDepartment.parent_department_id], back_populates='parent_department', lazy='dynamic', cascade='all')  # 父部门
    child_department = db.relationship('RelDepartment', foreign_keys=[RelDepartment.child_department_id], back_populates='child_department', lazy='dynamic', cascade='all')     # 子部门
    # 设置父部门
    def set_parent_department(self, department):
        '''
        逻辑：首先判断是否已经维护父部门，如果存在则执行删除后新增
        :param dept:
        :return:
        '''
        ref = RelDepartment.query.filter_by(child_department_id=self.id).first()
        if ref:
            db.session.delete(ref)
            db.session.commit()
        parent = RelDepartment(id=uuid.uuid4().hex, child_department=self, parent_department=department)
        db.session.add(parent)
        db.session.commit()
    @property
    def get_parent_department(self):
        dept = RelDepartment.query.filter_by(child_department_id=self.id).first()
        return dept.parent_department if dept else None
    # 设置子部门
    def set_child_department(self, department):
        '''
        逻辑：首先解除子部门原有的部门关系，然后再添加到当前部门下
        :param dept:
        :return:
        '''
        ref = RelDepartment.query.filter_by(child_department_id=department.id).first()
        if ref:
            db.session.delete(ref)
            db.session.commit()
        child = RelDepartment(id=uuid.uuid4().hex, child_department=department, parent_department=self)
        db.session.add(child)
        db.session.commit()
    @property
    def get_child_department(self):
        return RelDepartment.query.filter_by(parent_department_id=self.id).order_by(RelDepartment.createtime_loc.desc()).all()
'''
雇员信息
'''
class BizEmployee(BaseModel, db.Model):
    code = db.Column(db.String(32))     # 职号
    name = db.Column(db.String(128))    # 姓名
    email = db.Column(db.String(128))   # 邮箱
    phone = db.Column(db.String(20))    # 电话
    company_id = db.Column(db.String(32), db.ForeignKey('biz_company.id'))          # 所属法人ID
    company = db.relationship('BizCompany', back_populates='employees')             # 所属法人
    department_id = db.Column(db.String(32), db.ForeignKey('biz_department.id'))    # 所属部门ID
    department = db.relationship('BizDepartment', back_populates='employees')       # 所属部门