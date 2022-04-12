import pymssql
from flask import current_app
def get_connection():
    connection = pymssql.connect(server=current_app.config['GSR_SERVER'],
                              user=current_app.config['GSR_USER'],
                              password=current_app.config['GSR_PASSWORD'],
                              database=current_app.config['GSR_DATABASE'])
    return connection
def get_code_master():
    '''
        获取GSR安保基础数据
        :return:
    '''
    connection = get_connection()
    cursor = connection.cursor()
    if cursor:
        print('GSR数据库MS SQLServer连接成功......')
    else:
        print('GSR数据库MS SQLServer连接失败......')
    sql = '''
       select rootorgunitid     --法人代码
           ,upperorgunitid      --上级部门代码    
           ,orgunitid           --部门代码
           ,deptshortname       --部门名称
       from viewghrisdeptmaster2
       where 1 = 1
       and rootorgunitid <>upperorgunitid
       and upperorgunitid <> '03000001'
       and rootorgunitid in ('01920601','01920773','01920052','01920000')        
   '''
    '''cursor.execute(sql)
    departments = []
    print('-' * 80)
    for row in cursor:
        departments.append((row[0], row[1], row[2], row[3]))
    cursor.close()
    connection.close()
    return tuple(departments)'''
def get_gsr_data():
    '''
        获取GSR处理数据：只获取当天处理完成的数据
        :return:
    '''
    connection = get_connection()
    cursor = connection.cursor()
    if cursor:
        print('GSR数据库MS SQLServer连接成功......')
    else:
        print('GSR数据库MS SQLServer连接失败......')
    sql = '''
        select 
            b.rootorgunitid as company_id           --法人代码
            ,a.orgunitid as department_code         --部门代码            
            ,a.userid as employee_code              --雇员职号
            ,a.name_zh as employee_name             --雇员姓名
            ,a.employeestatus as employee_status    --在职状态
            ,a.mail as employee_email               --邮箱地址
            ,a.mobilenumber as employee_phone       --电话号码
        from viewghrisusermaster2_china a
        left join viewghrisdeptmaster2 b on a.orgunitid = b.orgunitid
        where 1 = 1
        and a.orgunitid is not null
        and a.userid <> ''        
        and a.orgunitid <> b.rootorgunitid
        and b.rootorgunitid in ('01920601','01920773','01920052','01920000')
    '''
    '''cursor.execute(sql)
    employees = []
    print('-' * 80)
    for row in cursor:
        employees.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6]))
    cursor.close()
    connection.close()
    return tuple(employees)'''