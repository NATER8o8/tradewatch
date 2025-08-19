
from alembic import op
import sqlalchemy as sa
revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None
def upgrade():
    op.create_table('officials',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('chamber', sa.Enum('house','senate','executive','other', name='chamber'), nullable=True),
        sa.Column('role', sa.String(length=200), nullable=True, server_default=''),
        sa.Column('state', sa.String(length=50), nullable=True, server_default=''),
        sa.Column('committees', sa.Text(), nullable=True, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    op.create_table('trades',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('official_id', sa.Integer(), sa.ForeignKey('officials.id')),
        sa.Column('filing_url', sa.Text(), nullable=True, server_default=''),
        sa.Column('transaction_type', sa.Enum('buy','sell','exchange','unknown', name='txtype'), nullable=True),
        sa.Column('owner', sa.Enum('self','spouse','dependent','joint','unknown', name='owner'), nullable=True),
        sa.Column('trade_date', sa.Date(), nullable=True),
        sa.Column('reported_date', sa.Date(), nullable=True),
        sa.Column('ticker', sa.String(length=32), nullable=True, server_default=''),
        sa.Column('issuer', sa.String(length=256), nullable=True, server_default=''),
        sa.Column('amount_min', sa.Numeric(18,2), nullable=True),
        sa.Column('amount_max', sa.Numeric(18,2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))
    )
def downgrade():
    op.drop_table('trades')
    op.drop_table('officials')
