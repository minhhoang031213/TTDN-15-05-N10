from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

class DonXinLamNgoaiGio(models.Model):
    _name = 'don.xin.lam.ngoai.gio'
    _description = 'Đơn xin làm ngoài giờ'
    _order = 'ngay_lam desc, id desc'

    name = fields.Char(string='Số đơn', readonly=True, copy=False, default='New')
    nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân viên', required=True)
    phong_ban_id = fields.Many2one('phong_ban', string='Phòng ban', related='nhan_vien_id.phong_ban_id', store=True)
    
    ngay_lam = fields.Date(string='Ngày làm', required=True, default=fields.Date.context_today)
    gio_bat_dau = fields.Datetime("Giờ đăng ký vào", required=True, help="Chọn giờ vào")
    gio_ket_thuc = fields.Datetime("Giờ đăng ký về", required=True, help="Chọn giờ ra")
    so_gio = fields.Float(string='Số giờ', compute='_compute_so_gio', store=True)
    
    ly_do = fields.Text(string='Lý do', required=True)
    trang_thai = fields.Selection([
        ('draft', 'Nháp'),
        ('submitted', 'Đã gửi'),
        ('approved', 'Đã duyệt'),
        ('rejected', 'Từ chối')
    ], string='Trạng thái', default='draft')

    ngay_duyet = fields.Datetime(string='Ngày duyệt', readonly=True)
    ghi_chu = fields.Text(string='Ghi chú')

    file_dinh_kem = fields.Binary("Tệp đính kèm")
    file_ten = fields.Char("Tên tệp")

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('don.xin.lam.ngoai.gio') or 'New'
        return super(DonXinLamNgoaiGio, self).create(vals)

    @api.depends('gio_bat_dau', 'gio_ket_thuc')
    def _compute_so_gio(self):
        for record in self:
            if record.gio_bat_dau and record.gio_ket_thuc:
                if record.gio_ket_thuc > record.gio_bat_dau:
                    record.so_gio = record.gio_ket_thuc - record.gio_bat_dau
                else:
                    record.so_gio = 0
            else:
                record.so_gio = 0

    @api.constrains('gio_bat_dau', 'gio_ket_thuc')
    def _check_gio(self):
        for record in self:
            if record.gio_bat_dau and record.gio_ket_thuc:
                if record.gio_bat_dau >= record.gio_ket_thuc:
                    raise ValidationError('Giờ kết thúc phải lớn hơn giờ bắt đầu!')
                if record.gio_bat_dau < 0 or record.gio_bat_dau > 24:
                    raise ValidationError('Giờ bắt đầu không hợp lệ!')
                if record.gio_ket_thuc < 0 or record.gio_ket_thuc > 24:
                    raise ValidationError('Giờ kết thúc không hợp lệ!')

    def action_submit(self):
        self.write({'trang_thai': 'submitted'})

    def action_approve(self):
        self.write({
            'trang_thai': 'approved',
            'nguoi_duyet_id': self.env.user.id,
            'ngay_duyet': fields.Datetime.now()
        })

    def action_reject(self):
        self.write({
            'trang_thai': 'rejected',
            'nguoi_duyet_id': self.env.user.id,
            'ngay_duyet': fields.Datetime.now()
        })

