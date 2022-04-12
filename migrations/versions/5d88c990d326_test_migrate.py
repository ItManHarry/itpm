"""test migrate

Revision ID: 5d88c990d326
Revises: 
Create Date: 2022-04-07 15:07:01.582201

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5d88c990d326'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('biz_employee', sa.Column('test', sa.String(length=12), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('biz_employee', 'test')
    # ### end Alembic commands ###