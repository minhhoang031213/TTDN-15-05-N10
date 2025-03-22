from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ThongKeChamCong(models.Model):
    _name = 'thong_ke_cham_cong'
    _description = 'Thống kê chấm công'
    _order = 'ngay desc, nhan_vien_id'

    nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân viên', required=True)
    phong_ban_id = fields.Many2one('phong_ban', string='Phòng ban', related='nhan_vien_id.phong_ban_id', store=True)
    ngay = fields.Date(string='Ngày', required=True, default=fields.Date.context_today)
    thang = fields.Selection([(str(i), f'Tháng {i}') for i in range(1, 13)], string='Tháng', compute='_compute_thang_nam', store=True)
    nam = fields.Integer(string='Năm', compute='_compute_thang_nam', store=True)

    so_ngay_cong = fields.Integer(string='Số ngày đi làm', compute='_compute_thong_ke_ngay', store=True)
    so_ngay_nghi = fields.Integer(string='Số ngày nghỉ', compute='_compute_thong_ke_ngay', store=True)
    so_gio_trung_binh = fields.Float(string='Số giờ trung bình', compute='_compute_thong_ke_ngay', store=True, digits=(10, 2))
    so_gio_lam_them = fields.Float(string='Số giờ làm thêm', compute='_compute_thong_ke_ngay', store=True, digits=(10, 2))
    so_ngay_di_muon = fields.Integer(string="Số ngày đi muộn", compute='_compute_thong_ke_ngay', store=True)
    so_ngay_ve_som = fields.Integer(string="Số ngày về sớm", compute='_compute_thong_ke_ngay', store=True)
    
    tong_so_nhan_vien = fields.Integer(string='Tổng số nhân viên', compute='_compute_thong_ke_phong_ban', store=True)
    so_nhan_vien_di_lam = fields.Integer(string='Số nhân viên đi làm', compute='_compute_thong_ke_phong_ban', store=True)
    so_nhan_vien_nghi = fields.Integer(string='Số nhân viên nghỉ', compute='_compute_thong_ke_phong_ban', store=True)
    ti_le_di_lam = fields.Float(string='Tỷ lệ đi làm', compute='_compute_thong_ke_phong_ban', store=True, digits=(5, 2))

    @api.depends('ngay')
    def _compute_thang_nam(self):
        for record in self:
            if record.ngay:
                record.thang = str(record.ngay.month)
                record.nam = record.ngay.year

    @api.depends('nhan_vien_id', 'ngay')
    def _compute_thong_ke_ngay(self):
        for record in self:
            if not record.nhan_vien_id or not record.ngay:
                continue

            # Lấy tất cả bản ghi chấm công của nhân viên trong ngày
            cham_cong_ids = self.env['cham_cong'].search([
                ('nhan_vien_id', '=', record.nhan_vien_id.id),
                ('ngay_lam', '=', record.ngay)
            ])

            # Tính toán thống kê
            record.so_ngay_cong = len(cham_cong_ids.filtered(lambda x: x.trang_thai_lam_viec == 'da_lam_viec'))
            record.so_ngay_nghi = len(cham_cong_ids.filtered(lambda x: x.trang_thai_lam_viec == 'chua_bat_dau'))
            record.so_ngay_di_muon = len(cham_cong_ids.filtered(lambda x: x.phut_di_lam_muon > 0))
            record.so_ngay_ve_som = len(cham_cong_ids.filtered(lambda x: x.phut_di_lam_som > 0))

            # Tính giờ làm
            tong_gio = sum(cham_cong.thoi_gian_lam_viec for cham_cong in cham_cong_ids)
            record.so_gio_trung_binh = tong_gio / len(cham_cong_ids) if cham_cong_ids else 0
            # Tạm thời bỏ qua số giờ làm thêm vì chưa có trường này
            record.so_gio_lam_them = 0

    @api.depends('phong_ban_id', 'ngay')
    def _compute_thong_ke_phong_ban(self):
        for record in self:
            if not record.phong_ban_id or not record.ngay:
                continue

            # Lấy tất cả nhân viên trong phòng ban
            nhan_vien_ids = self.env['nhan_vien'].search([('phong_ban_id', '=', record.phong_ban_id.id)])
            record.tong_so_nhan_vien = len(nhan_vien_ids)

            # Lấy tất cả bản ghi chấm công của phòng ban trong ngày
            cham_cong_ids = self.env['cham_cong'].search([
                ('nhan_vien_id', 'in', nhan_vien_ids.ids),
                ('ngay_lam', '=', record.ngay)
            ])

            # Tính toán thống kê
            record.so_nhan_vien_di_lam = len(cham_cong_ids.filtered(lambda x: x.trang_thai_lam_viec == 'da_lam_viec'))
            record.so_nhan_vien_nghi = len(cham_cong_ids.filtered(lambda x: x.trang_thai_lam_viec == 'chua_bat_dau'))
            
            # Tính tỷ lệ đi làm
            if record.tong_so_nhan_vien > 0:
                record.ti_le_di_lam = (record.so_nhan_vien_di_lam / record.tong_so_nhan_vien) * 100
            else:
                record.ti_le_di_lam = 0.0

    _sql_constraints = [
        ('unique_nhan_vien_ngay', 'unique(nhan_vien_id, ngay)', 'Mỗi nhân viên chỉ được có một bản ghi chấm công trong một ngày!')
    ]
