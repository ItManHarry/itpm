from pm.plugins import scheduler, db
from pm.models import SysUser, SysLog, BizDepartment, BizCompany, RelDepartment, BizEmployee
import uuid, time
from datetime import datetime
from pm.infs.If_GSR import get_gsr_data, get_code_master
def synchronize_gsr_data_job():
    '''
    同步GSR安保代码基本信息&GSR处理数据
    :return:
    '''
    # 使用上下文，否则报错
    with scheduler.app.app_context():
        app = scheduler.app
        user = SysUser.query.filter_by(user_id='admin').first()
        print('-' * 80)
        # 获取法人代码/ID map关系
        code = get_code_master()
        gsr = get_gsr_data()
        # 写入日志
        user = SysUser.query.filter_by(user_id='admin').first()
        log = SysLog(id=uuid.uuid4().hex, url='null', operation='GSR数据同步成功', create_id=user.id, user_id=user.id)
        db.session.add(log)
        db.session.commit()