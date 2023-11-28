"""Follow Implementaion

Revision ID: 97ac0ba81da8
Revises: 756ffa77f8d2
Create Date: 2023-11-07 16:48:46.968807

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import app.models.guid

# revision identifiers, used by Alembic.
revision: str = '97ac0ba81da8'
down_revision: Union[str, None] = '756ffa77f8d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('follow',
    sa.Column('id', app.models.guid.GUID(), nullable=False),
    sa.Column('accept_status', sa.Integer(), nullable=False),
    sa.Column('following_user_id', app.models.guid.GUID(), nullable=False),
    sa.Column('followed_user_id', app.models.guid.GUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("TIMEZONE('utc', CURRENT_TIMESTAMP)"), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("TIMEZONE('utc', CURRENT_TIMESTAMP)"), nullable=False),
    sa.ForeignKeyConstraint(['followed_user_id'], ['user.id'], name=op.f('fk_follow_followed_user_id_user'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['following_user_id'], ['user.id'], name=op.f('fk_follow_following_user_id_user'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_follow'))
    )
    op.create_index(op.f('ix_follow_followed_user_id'), 'follow', ['followed_user_id'], unique=False)
    op.create_index(op.f('ix_follow_following_user_id'), 'follow', ['following_user_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_follow_following_user_id'), table_name='follow')
    op.drop_index(op.f('ix_follow_followed_user_id'), table_name='follow')
    op.drop_table('follow')
    # ### end Alembic commands ###
