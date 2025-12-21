from unittest.util import _MAX_LENGTH
from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from .utils import rename_imagefile_to_uuid

# 24.02.24 잘못된 유저 중복 제거
# from django.contrib.auth.models import (
#     BaseUserManager, AbstractBaseUser
# )

# class Profile(models.Model):
# 	user = models.OneToOneField(User, on_delete=models.CASCADE)
# 	# user model 과 1:1 의 관계임을 나타냄

 
# class UserManager(BaseUserManager):
#     def create_user(self, email, BIZ_NO, password=None):
#         if not email:
#             raise ValueError('회원가입을 위해 이메일주소를 입력해주시기 바랍니다.')
#         user = self.model(
#             email = self.normalize_email(email),
#             BIZ_NO = BIZ_NO,
#         )
#         user.set_password(password)
#         user.save(using=self._db)
#         return user

#     def create_superuser(self, email, BIZ_NO, password):
#         user = self.create_user(
#             email,
#             password=password,
#             BIZ_NO=BIZ_NO,
#         )
#         user.is_admin = True
#         user.save(using=self._db)
#         return user

# class User(AbstractBaseUser):
#     email = models.EmailField(
#         verbose_name='이메일주소',
#         max_length=255,
#         unique=True,
#     )
#     BIZ_NO = models.CharField(
#         verbose_name='사업자번호',
#         max_length=30,
#         unique=True
#     )
#     is_active = models.BooleanField(default=True)
#     is_admin = models.BooleanField(default=False)

#     objects = UserManager()

#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ['BIZ_NO']

#     def get_full_name(self):
#         # The user is identified by their email address
#         return self.email

#     def get_short_name(self):
#         # The user is identified by their email address
#         return self.email

#     def __str__(self):              # __unicode__ on Python 2
#         return self.email

#     def has_perm(self, perm, obj=None):
#         "Does the user have a specific permission?"
#         # Simplest possible answer: Yes, always
#         return True

#     def has_module_perms(self, app_label):
#         "Does the user have permissions to view the app `app_label`?"
#         # Simplest possible answer: Yes, always
#         return True

#     @property
#     def is_staff(self):
#         "Is the user a member of staff?"
#         # Simplest possible answer: All admins are staff
#         return self.is_admin


class AuthUser(models.Model):
    password = models.CharField(max_length=128, db_collation='Korean_Wansung_CI_AS')
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150, db_collation='Korean_Wansung_CI_AS')
    first_name = models.CharField(max_length=150, db_collation='Korean_Wansung_CI_AS')
    last_name = models.CharField(max_length=150, db_collation='Korean_Wansung_CI_AS')
    email = models.CharField(max_length=254, db_collation='Korean_Wansung_CI_AS')
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150, db_collation='Korean_Wansung_CI_AS')

    class Meta:
        managed = False
        db_table = 'auth_group'
class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS')
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS')

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)

class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)



class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)

class userProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', null=True)
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to=rename_imagefile_to_uuid, max_length=255)
    description = models.CharField(max_length=500)
    image_thumbnail = ImageSpecField(source='image', processors=[ResizeToFill(120, 120)])
    class Meta:
        managed = False
        db_table = 'app_userprofile'
    def __str__(self):
        return self.title


# simplebook DB
class AcntItemcd(models.Model):
    acnt_cd = models.CharField(db_column='Acnt_Cd', primary_key=True, max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    aply_dt = models.CharField(db_column='Aply_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    end_dt = models.CharField(db_column='End_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    placnt_nm = models.CharField(db_column='PlAcnt_Nm', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trnacnt_nm = models.CharField(db_column='TrnAcnt_Nm', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_nm = models.CharField(db_column='Acnt_Nm', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_attrb = models.CharField(db_column='Acnt_Attrb', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    prt_ord = models.IntegerField(db_column='Prt_Ord')  # Field name made lowercase.
    tot_acnt_cd = models.CharField(db_column='Tot_Acnt_Cd', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    bookdp_attrb = models.CharField(db_column='BookDp_Attrb', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_gbattrb = models.CharField(db_column='Acnt_GbAttrb', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    chg_dt = models.CharField(db_column='Chg_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Acnt_ItemCd'


class ActAsset(models.Model):
    tran_dt = models.CharField(db_column='Tran_Dt', primary_key=True, max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    seq_no = models.CharField(db_column='Seq_No', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_no = models.CharField(db_column='Ibo_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='Acnt_Cd', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_stat = models.CharField(db_column='Tran_Stat', max_length=7, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_amt = models.DecimalField(db_column='Tran_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    remk = models.CharField(db_column='Remk', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    disposal_dt = models.CharField(db_column='Disposal_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    disposal_amt = models.DecimalField(db_column='Disposal_Amt', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    disuse_dt = models.CharField(db_column='Disuse_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    disuse_amt = models.DecimalField(db_column='Disuse_Amt', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    refnd_amt = models.DecimalField(db_column='Refnd_Amt', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    lastrefnd_dt = models.CharField(db_column='LastRefnd_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    slip_no = models.CharField(db_column='Slip_No', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    slip_trandt = models.CharField(db_column='Slip_TranDt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Act_Asset'
        unique_together = (('tran_dt', 'seq_no', 'ibo_no', 'acnt_cd'),)


class ActAssettrn(models.Model):
    tran_dt = models.CharField(db_column='Tran_Dt', primary_key=True, max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    seq_no = models.CharField(db_column='Seq_No', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trnseq_no = models.CharField(db_column='TrnSeq_No', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_no = models.CharField(db_column='Ibo_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='Acnt_Cd', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_stat = models.CharField(db_column='Tran_Stat', max_length=7, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_amt = models.DecimalField(db_column='Tran_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    trnremk = models.CharField(db_column='TrnRemk', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    slip_no = models.CharField(db_column='Slip_No', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    slip_trandt = models.CharField(db_column='Slip_TranDt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Act_AssetTrn'
        unique_together = (('tran_dt', 'seq_no', 'trnseq_no', 'ibo_no', 'acnt_cd'),)


class ActCode(models.Model):
    kind_cd = models.CharField(db_column='Kind_Cd', primary_key=True, max_length=7, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    kind_cd_1 = models.CharField(db_column='Kind_Cd_1', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    kind_cd_2 = models.CharField(db_column='Kind_Cd_2', max_length=3, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    kind_cd_ds = models.CharField(db_column='Kind_Cd_Ds', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Act_Code'


class ActDistributetrn(models.Model):
    tran_dt = models.CharField(db_column='Tran_Dt', primary_key=True, max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_no = models.CharField(db_column='Ibo_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    seq_no = models.CharField(db_column='Seq_No', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_stat = models.CharField(db_column='Tran_Stat', max_length=7, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    gubun_ty = models.CharField(db_column='Gubun_TY', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_amt = models.DecimalField(db_column='Tran_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    co_rgst_no = models.CharField(db_column='Co_Rgst_No', max_length=13, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    co_rgst_nm = models.CharField(db_column='Co_Rgst_Nm', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    gong_type = models.CharField(db_column='Gong_Type', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    slip_no = models.CharField(db_column='Slip_No', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    slip_trandt = models.CharField(db_column='Slip_TranDt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    exempseq_no = models.CharField(db_column='ExempSeq_No', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Act_DistributeTrn'
        unique_together = (('tran_dt', 'ibo_no', 'seq_no'),)


class ActGeralledgr(models.Model):
    tran_dt = models.CharField(db_column='Tran_Dt', primary_key=True, max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_no = models.CharField(db_column='IBO_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='Acnt_Cd', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    bal = models.DecimalField(db_column='Bal', max_digits=13, decimal_places=0)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Act_Geralledgr'
        unique_together = (('tran_dt', 'ibo_no', 'acnt_cd'),)


class ActSaleAcount(models.Model):
    crt_dt = models.CharField(db_column='Crt_Dt', primary_key=True, max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    crt_serno = models.CharField(db_column='Crt_Serno', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    crt_gubun = models.CharField(db_column='Crt_Gubun', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_stat = models.CharField(db_column='Tran_Stat', max_length=7, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    slip_tran_dt = models.CharField(db_column='Slip_Tran_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    slip_no = models.CharField(db_column='Slip_No', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_no = models.CharField(db_column='IBO_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    bill_kind = models.CharField(db_column='Bill_Kind', max_length=7, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    cust_id = models.CharField(db_column='Cust_Id', max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    cust_nm = models.CharField(db_column='Cust_Nm', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    tran_amt = models.DecimalField(db_column='Tran_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    supply_amt = models.DecimalField(db_column='Supply_Amt', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    extra_amt = models.DecimalField(db_column='Extra_Amt', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    extra_fixdt = models.CharField(db_column='Extra_FixDt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    extra_fixgb = models.CharField(db_column='Extra_FixGB', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    chg_dt = models.CharField(db_column='Chg_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    intax = models.DecimalField(db_column='Intax', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    rsdtax = models.DecimalField(db_column='Rsdtax', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    chkyn = models.CharField(db_column='ChkYN', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    costsales = models.DecimalField(db_column='CostSales', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    costsales_vat = models.DecimalField(db_column='COSTSALES_Vat', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    sale_dist = models.CharField(db_column='sale_Dist', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    recptspec = models.CharField(db_column='RecptSpec', max_length=2, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    trader_rep = models.CharField(db_column='Trader_Rep', max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    trader_offaddr = models.CharField(db_column='Trader_OffAddr', max_length=200, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Act_Sale_Acount'
        unique_together = (('crt_dt', 'crt_serno', 'crt_gubun', 'ibo_no'),)


class ActSlipacnt(models.Model):
    tran_dt = models.CharField(db_column='Tran_Dt', primary_key=True, max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_no = models.CharField(db_column='IBO_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    slip_no = models.CharField(db_column='Slip_No', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='Acnt_Cd', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_amt = models.DecimalField(db_column='Acnt_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Act_SlipAcnt'
        unique_together = (('tran_dt', 'ibo_no', 'slip_no'),)


class ActSlipledgr(models.Model):
    tran_dt = models.CharField(db_column='Tran_Dt', primary_key=True, max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_no = models.CharField(db_column='IBO_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    slip_no = models.CharField(db_column='Slip_No', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_knd = models.CharField(db_column='Tran_Knd', max_length=7, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    onlin_yn = models.CharField(db_column='Onlin_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_tm = models.CharField(db_column='Tran_Tm', max_length=6, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_stat = models.CharField(db_column='Tran_Stat', max_length=7, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_amt = models.DecimalField(db_column='Tran_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    remk = models.CharField(db_column='Remk', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    cncl_dt = models.CharField(db_column='Cncl_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    cncl_man = models.CharField(db_column='Cncl_Man', max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Act_SlipLedgr'
        unique_together = (('tran_dt', 'ibo_no', 'slip_no'),)


class BkDsSlipledgr20417(models.Model):
    seq_no = models.CharField(db_column='Seq_No', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    work_yy = models.CharField(db_column='Work_YY', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='Acnt_cd', max_length=3, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_nm = models.CharField(db_column='Acnt_Nm', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_dt = models.CharField(db_column='Tran_Dt', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    remk = models.CharField(db_column='Remk', max_length=500, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_code = models.CharField(db_column='Trader_Code', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_name = models.CharField(db_column='Trader_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_bizno = models.CharField(db_column='Trader_Bizno', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    slip_no = models.CharField(db_column='Slip_No', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_stat = models.CharField(db_column='Tran_Stat', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crdr = models.CharField(db_column='CrDr', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tranamt_cr = models.DecimalField(db_column='TranAmt_Cr', max_digits=15, decimal_places=0)  # Field name made lowercase.
    tranamt_dr = models.DecimalField(db_column='TranAmt_Dr', max_digits=15, decimal_places=0)  # Field name made lowercase.
    employee_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    employee_name = models.CharField(db_column='employee_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    credit_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    credit_name = models.CharField(db_column='credit_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    place_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    place_name = models.CharField(db_column='place_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    project_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    project_name = models.CharField(db_column='project_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    cncl_dt = models.CharField(db_column='Cncl_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'BK_ds_slipledgr2_0417'


class BfincomeList(models.Model):
    yy = models.CharField(db_column='YY', primary_key=True, max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_no = models.CharField(db_column='Ibo_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    seq_no = models.CharField(db_column='Seq_No', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    std_incm_rt_dd = models.CharField(db_column='Std_Incm_Rt_Dd', max_length=6, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    busnsect_nm = models.CharField(db_column='Busnsect_Nm', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    bfincome_amt = models.DecimalField(db_column='BfIncome_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    mdfy_dt = models.CharField(db_column='Mdfy_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'BfIncome_List'
        unique_together = (('yy', 'ibo_no', 'seq_no'),)


class BodBoard(models.Model):
    seq_no = models.AutoField(db_column='Seq_No', primary_key=True)  # Field name made lowercase.
    re_seq = models.IntegerField(db_column='Re_Seq')  # Field name made lowercase.
    flag = models.CharField(db_column='Flag', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    sub_flag = models.CharField(db_column='Sub_Flag', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    protect_yn = models.CharField(db_column='Protect_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    title = models.TextField(db_column='Title', db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    content = models.TextField(db_column='Content', db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase. This field type is a guess.
    contact = models.CharField(db_column='Contact', max_length=13, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    email = models.CharField(db_column='Email', max_length=40, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    writer = models.CharField(db_column='Writer', max_length=12, db_collation='Korean_Wansung_CS_AS')  # Field name made lowercase.
    password = models.CharField(db_column='Password', max_length=40, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    up_file = models.CharField(db_column='Up_File', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    view_no = models.IntegerField(db_column='View_No')  # Field name made lowercase.
    reg_date = models.DateTimeField(db_column='Reg_Date')  # Field name made lowercase.
    up_date = models.DateTimeField(db_column='Up_Date', blank=True, null=True)  # Field name made lowercase.
    re_yn = models.CharField(db_column='RE_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    del_yn = models.CharField(db_column='Del_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Bod_Board'


class CmsSemu(models.Model):
    seq_cms = models.CharField(db_column='seq_CMS', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    cms_name = models.CharField(db_column='CMS_name', max_length=200, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    seq_semu = models.CharField(db_column='seq_SEMU', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    semu_name = models.CharField(db_column='SEMU_name', max_length=200, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_no = models.CharField(max_length=12, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    splitcnt = models.CharField(db_column='splitCnt', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'CMS_SEMU'


class CmsSemusarangTrdst(models.Model):
    seq = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    seq_semu = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    semu_name = models.CharField(max_length=300, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    semu_bizno = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    semu_type = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'CMS_SEMUSARANG_TRDST'


class CmsSemuSuggest(models.Model):
    seq_cms = models.CharField(db_column='seq_CMS', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    cms_name = models.CharField(db_column='CMS_name', max_length=200, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    seq_semu = models.CharField(db_column='seq_SEMU', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    semu_name = models.CharField(db_column='SEMU_name', max_length=200, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_no = models.CharField(max_length=12, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    splitcnt = models.CharField(db_column='splitCnt', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'CMS_SEMU_Suggest'


class CmsTemp(models.Model):
    seq = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    예정일 = models.CharField(max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    출금일 = models.CharField(max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    회원번호 = models.CharField(max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    회원명 = models.CharField(max_length=300, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    약정일 = models.CharField(max_length=2, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신청금액 = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    출금금액 = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    신청구분 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    출금상태 = models.CharField(max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    은행 = models.CharField(max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    결재계좌번호 = models.CharField(max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    주민사업자번호 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    회원구분 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    관리자 = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    등록일자 = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    연락처 = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    비고 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    seq_semu = models.CharField(db_column='seq_SEMU', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'CMS_Temp'


class CalcHealthInsu(models.Model):
    seq_no = models.AutoField(db_column='Seq_No', primary_key=True)  # Field name made lowercase.
    ibo_no = models.CharField(db_column='Ibo_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    flag = models.CharField(db_column='Flag', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    sel_kap = models.DecimalField(db_column='Sel_Kap', max_digits=13, decimal_places=0)  # Field name made lowercase.
    reg_date = models.DateTimeField(db_column='Reg_date')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Calc_Health_Insu'


class ConsultBoard(models.Model):
    num = models.IntegerField(blank=True, null=True)
    dbl = models.CharField(db_column='DBL', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    sbl = models.CharField(db_column='SBL', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    depth = models.IntegerField()
    isfolder = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS')
    uli = models.CharField(db_column='ULI', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    rank = models.IntegerField(db_column='RANK', blank=True, null=True)  # Field name made lowercase.
    title1 = models.TextField(db_collation='Korean_Wansung_CI_AS')
    content1 = models.TextField(db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    title2 = models.TextField(db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    content2 = models.TextField(db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    title3 = models.TextField(db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    content3 = models.TextField(db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    content4 = models.TextField(db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    hit = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    regdate = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Consult_Board'




class DsSlipledgr(models.Model):
    seq_no = models.CharField(db_column='Seq_No', primary_key=True, max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    work_yy = models.CharField(db_column='Work_YY', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='Acnt_cd', max_length=3, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_dt = models.CharField(db_column='Tran_Dt', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    remk = models.CharField(db_column='Remk', max_length=500, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_code = models.CharField(db_column='Trader_Code', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_name = models.CharField(db_column='Trader_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_bizno = models.CharField(db_column='Trader_Bizno', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    slip_no = models.CharField(db_column='Slip_No', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    onlin_yn = models.CharField(db_column='Onlin_YN', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_stat = models.CharField(db_column='Tran_Stat', max_length=7, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    crdr = models.CharField(db_column='CrDr', max_length=2, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_amt = models.DecimalField(db_column='Tran_Amt', max_digits=15, decimal_places=0)  # Field name made lowercase.
    cncl_dt = models.CharField(db_column='Cncl_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'DS_SlipLedgr'
        unique_together = (('seq_no', 'work_yy', 'acnt_cd', 'tran_dt', 'slip_no', 'crdr'),)


class DsSlipledgr2(models.Model):
    seq_no = models.CharField(db_column='Seq_No', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    work_yy = models.CharField(db_column='Work_YY', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='Acnt_cd', max_length=3, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_nm = models.CharField(db_column='Acnt_Nm', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_dt = models.CharField(db_column='Tran_Dt', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    remk = models.CharField(db_column='Remk', max_length=500, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_code = models.CharField(db_column='Trader_Code', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_name = models.CharField(db_column='Trader_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_bizno = models.CharField(db_column='Trader_Bizno', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    slip_no = models.CharField(db_column='Slip_No', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_stat = models.CharField(db_column='Tran_Stat', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crdr = models.CharField(db_column='CrDr', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tranamt_cr = models.DecimalField(db_column='TranAmt_Cr', max_digits=15, decimal_places=0)  # Field name made lowercase.
    tranamt_dr = models.DecimalField(db_column='TranAmt_Dr', max_digits=15, decimal_places=0)  # Field name made lowercase.
    employee_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    employee_name = models.CharField(db_column='employee_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    credit_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    credit_name = models.CharField(db_column='credit_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    place_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    place_name = models.CharField(db_column='place_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    project_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    project_name = models.CharField(db_column='project_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    cncl_dt = models.CharField(db_column='Cncl_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'DS_SlipLedgr2'


class DsSlipledgr2Feedback(models.Model):
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    work_yy = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    tran_dt = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    acnt_cd = models.CharField(max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    acnt_nm = models.CharField(max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    slip_no = models.CharField(max_length=6, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    feedback = models.CharField(max_length=500, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    createdate = models.DateTimeField(db_column='createDate', blank=True, null=True)  # Field name made lowercase.
    isdispense = models.CharField(db_column='isDispense', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    dispensedate = models.DateTimeField(db_column='dispenseDate', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'DS_SlipLedgr2_Feedback'


class DsSlipledgrEcount(models.Model):
    seq_no = models.CharField(db_column='Seq_No', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    work_yy = models.CharField(db_column='Work_YY', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    work_qt = models.CharField(db_column='Work_QT', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    prt_ord = models.CharField(db_column='Prt_Ord', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='Acnt_cd', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_nm = models.CharField(db_column='Acnt_Nm', max_length=200, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    tran_dt = models.CharField(db_column='Tran_Dt', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    remk = models.CharField(db_column='Remk', max_length=500, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_code = models.CharField(db_column='Trader_Code', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_name = models.CharField(db_column='Trader_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_bizno = models.CharField(db_column='Trader_Bizno', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    slip_no = models.CharField(db_column='Slip_No', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    tran_stat = models.CharField(db_column='Tran_Stat', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crdr = models.CharField(db_column='CrDr', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tranamt = models.DecimalField(db_column='TranAmt', max_digits=15, decimal_places=0)  # Field name made lowercase.
    tranamt_cr = models.DecimalField(db_column='TranAmt_Cr', max_digits=15, decimal_places=0)  # Field name made lowercase.
    tranamt_dr = models.DecimalField(db_column='TranAmt_Dr', max_digits=15, decimal_places=0)  # Field name made lowercase.
    acnt_cd_org = models.CharField(db_column='Acnt_cd_ORG', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_nm_org = models.CharField(db_column='Acnt_Nm_ORG', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_code_org = models.CharField(db_column='Trader_Code_ORG', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_name_org = models.CharField(db_column='Trader_Name_ORG', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'DS_SlipLedgr_Ecount'


class DeferContribute(models.Model):
    seq_no = models.CharField(db_column='Seq_No', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_no = models.CharField(db_column='Ibo_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    contributecd = models.CharField(db_column='ContributeCD', max_length=2, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    creyy = models.CharField(db_column='CreYY', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    amortyy = models.CharField(db_column='AmortYY', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    incomeamt = models.DecimalField(db_column='IncomeAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    deleteyy = models.CharField(db_column='DeleteYY', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    deleteamt = models.DecimalField(db_column='DeleteAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    restamt = models.DecimalField(db_column='RestAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    mdfy_dt = models.CharField(db_column='Mdfy_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Defer_Contribute'


class DeferList(models.Model):
    yy = models.CharField(db_column='YY', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_no = models.CharField(db_column='Ibo_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    defercd = models.CharField(db_column='DeferCD', max_length=7, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    amortyy = models.CharField(db_column='AmortYY', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    targetamt = models.DecimalField(db_column='TargetAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    limitamt = models.DecimalField(db_column='LimitAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    overamt = models.DecimalField(db_column='OverAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    minusamt = models.DecimalField(db_column='MinusAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    restamt = models.DecimalField(db_column='RestAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    defercreyy = models.CharField(db_column='DeferCreYY', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    defertargetamt = models.DecimalField(db_column='DeferTargetAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    deferbfexpamt = models.DecimalField(db_column='DeferBfExpAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    deferafexpamt = models.DecimalField(db_column='DeferAfExpAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    deferrestamt = models.DecimalField(db_column='DeferRestAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    mdfy_dt = models.CharField(db_column='Mdfy_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Defer_List'


class DiagCapital(models.Model):
    seq_no = models.CharField(db_column='Seq_No', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    mh_name = models.CharField(db_column='MH_Name', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    mh_amt = models.DecimalField(db_column='MH_Amt', max_digits=15, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    mh_dcrate = models.CharField(db_column='MH_DcRate', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Diag_Capital'


class DiagTangibleasset(models.Model):
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    work_yy = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    acnt_cd = models.CharField(max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    tan_num = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    assetname = models.CharField(db_column='AssetName', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    gaindate = models.CharField(db_column='GainDate', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    gainamt = models.DecimalField(db_column='GainAmt', max_digits=15, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    busilamt = models.DecimalField(db_column='BusilAmt', max_digits=15, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    companyamt = models.DecimalField(db_column='CompanyAmt', max_digits=15, decimal_places=0, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Diag_TangibleAsset'


class DiagTotal(models.Model):
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    work_yy = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    diag_date = models.CharField(db_column='Diag_Date', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    acnt_cd = models.CharField(max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    acnt_nm = models.CharField(max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    tranamt_cr = models.DecimalField(db_column='TranAmt_Cr', max_digits=18, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    tranamt_dr = models.DecimalField(db_column='TranAmt_Dr', max_digits=18, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    prt_ord = models.IntegerField(db_column='Prt_Ord', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Diag_Total'


class Ds3245(models.Model):
    seq_no = models.CharField(db_column='Seq_No', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    work_yy = models.CharField(db_column='Work_YY', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='Acnt_cd', max_length=3, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_nm = models.CharField(db_column='Acnt_Nm', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_dt = models.CharField(db_column='Tran_Dt', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    remk = models.CharField(db_column='Remk', max_length=500, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_code = models.CharField(db_column='Trader_Code', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_name = models.CharField(db_column='Trader_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_bizno = models.CharField(db_column='Trader_Bizno', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    slip_no = models.CharField(db_column='Slip_No', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_stat = models.CharField(db_column='Tran_Stat', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crdr = models.CharField(db_column='CrDr', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tranamt_cr = models.DecimalField(db_column='TranAmt_Cr', max_digits=15, decimal_places=0)  # Field name made lowercase.
    tranamt_dr = models.DecimalField(db_column='TranAmt_Dr', max_digits=15, decimal_places=0)  # Field name made lowercase.
    employee_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    employee_name = models.CharField(db_column='employee_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    credit_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    credit_name = models.CharField(db_column='credit_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    place_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    place_name = models.CharField(db_column='place_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    project_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    project_name = models.CharField(db_column='project_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    cncl_dt = models.CharField(db_column='Cncl_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Ds_3245'


class ElecIncome(models.Model):
    ssn = models.CharField(db_column='SSN', max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    work_yy = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고구분상세코드 = models.CharField(max_length=2, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    종합소득금액 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득공제 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    종합소득_과세표준 = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    종합소득_세율 = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    종합소득_산출세액 = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    종합소득_세액감면 = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    종합소득_세액공제 = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    종합소득_결정세액 = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    종합소득_가산세 = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    종합소득_추가납부세액 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    종합소득_합계 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    종합소득_기납부세액 = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    종합소득_납부할총세액 = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    종합소득_납부특례세액_차감 = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    종합소득_납부특례세액_가산 = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    종합소득_분납할세액 = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    종합소득_신고기한내납부할세액 = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    지방소득세_과세표준 = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    지방소득세_세율 = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    지방소득세_산출세액 = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    지방소득세_기납부세액 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    지방소득세_납부할총세액 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    지방소득세_신고기한내납부할세액 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    농특세_과세표준 = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    농특세_세율 = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    농특세_산출세액 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    농특세_결정세액 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    농특세_가산세 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    농특세_환급세액 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    농특세_합계 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    농특세_기납부세액 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    농특세_납부할총세액 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    농특세_분납할세액 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    농특세_신고기한내납부할세액 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    비교과세적용구분코드 = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    지방소득세_세액감면 = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    지방소득세_세액공제 = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    지방소득세_결정세액 = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    지방소득세_가산세 = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    지방소득세_추가납부세액 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    지방소득세_합계 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Elec_Income'


class ElecInvoice(models.Model):
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    ofst_yn = models.CharField(db_column='ofst_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    prhslsclcd = models.CharField(db_column='prhSlsClCd', max_length=2, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    etxivclsfcd = models.CharField(db_column='etxivClsfCd', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    sumsplcft = models.DecimalField(db_column='sumSplCft', max_digits=15, decimal_places=0)  # Field name made lowercase.
    lsatsplcft = models.DecimalField(db_column='lsatSplCft', max_digits=15, decimal_places=0)  # Field name made lowercase.
    totaamt = models.DecimalField(db_column='totaAmt', max_digits=15, decimal_places=0)  # Field name made lowercase.
    lsatutprc = models.DecimalField(db_column='lsatUtprc', max_digits=15, decimal_places=0)  # Field name made lowercase.
    lsatqty = models.DecimalField(db_column='lsatQty', max_digits=15, decimal_places=0)  # Field name made lowercase.
    lsatnm = models.CharField(db_column='lsatNm', max_length=300, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    etxivsq1rmrkcntn = models.CharField(db_column='etxivSq1RmrkCntn', max_length=500, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    isntypecd = models.CharField(db_column='isnTypeCd', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    recapeclcd = models.CharField(db_column='recApeClCd', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    etxivkndcd = models.CharField(db_column='etxivKndCd', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    etan = models.CharField(primary_key=True, max_length=30, db_collation='Korean_Wansung_CI_AS')
    wrtdt = models.CharField(db_column='wrtDt', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tmsndt = models.CharField(db_column='tmsnDt', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    isndtm = models.CharField(db_column='isnDtm', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    rprsfnmb = models.CharField(db_column='rprsFnmB', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tnmnmb = models.CharField(db_column='tnmNmB', max_length=200, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    splrtxprdscmno = models.CharField(db_column='splrTxprDscmNo', max_length=14, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    adrb = models.CharField(db_column='adrB', max_length=500, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    mchrgemladrsls = models.CharField(db_column='mchrgEmlAdrSls', max_length=500, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    sumtxamt = models.DecimalField(db_column='sumTxamt', max_digits=15, decimal_places=0)  # Field name made lowercase.
    dmnrtxprdscmno = models.CharField(db_column='dmnrTxprDscmNo', max_length=14, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tnmnm = models.CharField(db_column='tnmNm', max_length=200, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    rprsfnm = models.CharField(db_column='rprsFnm', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    adr = models.CharField(max_length=500, db_collation='Korean_Wansung_CI_AS')
    mchrgemladrprh = models.CharField(db_column='mchrgEmlAdrPrh', max_length=500, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Elec_Invoice'


class FinancialAcntcd(models.Model):
    acnt_cd = models.CharField(db_column='Acnt_Cd', primary_key=True, max_length=3, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_nm = models.CharField(db_column='Acnt_Nm', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    aply_dt = models.CharField(db_column='Aply_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    end_dt = models.CharField(db_column='End_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_attrb = models.CharField(db_column='Acnt_Attrb', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_ty = models.IntegerField(db_column='Acnt_TY')  # Field name made lowercase.
    prt_ord = models.IntegerField(db_column='Prt_Ord')  # Field name made lowercase.
    tot_acnt_cd = models.CharField(db_column='Tot_Acnt_Cd', max_length=7, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crt_dt = models.DateTimeField(db_column='Crt_Dt', blank=True, null=True)  # Field name made lowercase.
    chg_dt = models.DateTimeField(db_column='Chg_Dt', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Financial_AcntCd'
        unique_together = (('acnt_cd', 'acnt_nm'),)


class FinancialAcntcdEcnt(models.Model):
    seq = models.IntegerField(blank=True, null=True)
    acntcd_semu = models.CharField(db_column='AcntCd_Semu', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acntnm_semu = models.CharField(db_column='AcntNm_Semu', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    acntcd_ecnt = models.CharField(db_column='AcntCd_Ecnt', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    acntnm_ecnt = models.CharField(db_column='AcntNm_Ecnt', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Financial_AcntCd_Ecnt'


class FinancialAcntnm(models.Model):
    financial_gb = models.CharField(db_column='Financial_GB', max_length=7, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_acntty = models.CharField(db_column='Financial_AcntTy', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_acntnm = models.CharField(db_column='Financial_AcntNm', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_trnacntnm = models.CharField(db_column='Financial_TrnAcntNm', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Financial_AcntNm'


class FinancialAcntnm2(models.Model):
    financial_gb = models.CharField(db_column='Financial_GB', max_length=7, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_acntty = models.CharField(db_column='Financial_AcntTy', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_acntnm = models.CharField(db_column='Financial_AcntNm', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_trnacntnm = models.CharField(db_column='Financial_TrnAcntNm', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_acntcd = models.CharField(db_column='Financial_AcntCd', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Financial_AcntNm2'


class FinancialCortax(models.Model):
    cortax_stndym = models.CharField(db_column='CorTax_StndYM', primary_key=True, max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    seq_no = models.CharField(max_length=12, db_collation='Korean_Wansung_CI_AS')
    work_amt0 = models.DecimalField(db_column='Work_Amt0', max_digits=18, decimal_places=3, blank=True, null=True)  # Field name made lowercase.
    work_amt1 = models.DecimalField(db_column='Work_Amt1', max_digits=18, decimal_places=3, blank=True, null=True)  # Field name made lowercase.
    work_amt2 = models.DecimalField(db_column='Work_Amt2', max_digits=18, decimal_places=3, blank=True, null=True)  # Field name made lowercase.
    work_amt3 = models.DecimalField(db_column='Work_Amt3', max_digits=18, decimal_places=3, blank=True, null=True)  # Field name made lowercase.
    work_amt4 = models.DecimalField(db_column='Work_Amt4', max_digits=18, decimal_places=3, blank=True, null=True)  # Field name made lowercase.
    work_amt5 = models.DecimalField(db_column='Work_Amt5', max_digits=18, decimal_places=3, blank=True, null=True)  # Field name made lowercase.
    work_amt6 = models.DecimalField(db_column='Work_Amt6', max_digits=18, decimal_places=3, blank=True, null=True)  # Field name made lowercase.
    work_amt7 = models.DecimalField(db_column='Work_Amt7', max_digits=18, decimal_places=3, blank=True, null=True)  # Field name made lowercase.
    work_amt8 = models.DecimalField(db_column='Work_Amt8', max_digits=18, decimal_places=3, blank=True, null=True)  # Field name made lowercase.
    work_amt9 = models.DecimalField(db_column='Work_Amt9', max_digits=18, decimal_places=3, blank=True, null=True)  # Field name made lowercase.
    work_amt10 = models.DecimalField(db_column='Work_Amt10', max_digits=18, decimal_places=3, blank=True, null=True)  # Field name made lowercase.
    work_amt11 = models.DecimalField(db_column='Work_Amt11', max_digits=18, decimal_places=3, blank=True, null=True)  # Field name made lowercase.
    work_amt12 = models.DecimalField(db_column='Work_Amt12', max_digits=18, decimal_places=3, blank=True, null=True)  # Field name made lowercase.
    work_amt13 = models.DecimalField(db_column='Work_Amt13', max_digits=18, decimal_places=3, blank=True, null=True)  # Field name made lowercase.
    work_amt14 = models.DecimalField(db_column='Work_Amt14', max_digits=18, decimal_places=3, blank=True, null=True)  # Field name made lowercase.
    work_amt15 = models.DecimalField(db_column='Work_Amt15', max_digits=18, decimal_places=3, blank=True, null=True)  # Field name made lowercase.
    crt_dt = models.DateTimeField(db_column='Crt_Dt', blank=True, null=True)  # Field name made lowercase.
    chg_dt = models.DateTimeField(db_column='Chg_Dt', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Financial_CorTax'
        unique_together = (('cortax_stndym', 'seq_no'),)


class FinancialOrigSheet(models.Model):
    financial_stnd_dt = models.CharField(db_column='Financial_STND_DT', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    seq_no = models.CharField(max_length=12, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    financial_gb = models.CharField(db_column='Financial_GB', max_length=7, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_fy = models.CharField(db_column='Financial_FY', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_fy_dt = models.CharField(db_column='Financial_FY_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_bf_fy = models.CharField(db_column='Financial_Bf_FY', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_bf_fy_dt = models.CharField(db_column='Financial_Bf_FY_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_serno = models.IntegerField(db_column='Financial_Serno', blank=True, null=True)  # Field name made lowercase.
    financial_acntnm = models.CharField(db_column='Financial_AcntNm', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_lamt = models.CharField(db_column='Financial_Lamt', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_ramt = models.CharField(db_column='Financial_Ramt', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_bf_lamt = models.CharField(db_column='Financial_Bf_Lamt', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_bf_ramt = models.CharField(db_column='Financial_Bf_Ramt', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_crt_dt = models.DateTimeField(db_column='Financial_Crt_Dt', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Financial_Orig_Sheet'


class FinancialSheet(models.Model):
    financial_stnd_dt = models.CharField(db_column='Financial_STND_DT', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    user_id = models.CharField(db_column='User_ID', max_length=12, db_collation='Korean_Wansung_CS_AS')  # Field name made lowercase.
    financial_gb = models.CharField(db_column='Financial_GB', max_length=7, db_collation='Korean_Wansung_CS_AS')  # Field name made lowercase.
    financial_fy = models.CharField(db_column='Financial_FY', primary_key=True, max_length=2, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    financial_fy_dt = models.CharField(db_column='Financial_FY_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    financial_bf_fy = models.CharField(db_column='Financial_Bf_FY', max_length=2, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    financial_bf_fy_dt = models.CharField(db_column='Financial_Bf_FY_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    financial_serno = models.IntegerField(db_column='Financial_Serno')  # Field name made lowercase.
    financial_acntcd = models.CharField(db_column='Financial_AcntCd', max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_acntnm = models.CharField(db_column='Financial_AcntNm', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    financial_lamt = models.CharField(db_column='Financial_Lamt', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    financial_ramt = models.CharField(db_column='Financial_Ramt', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    financial_bf_lamt = models.CharField(db_column='Financial_Bf_Lamt', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    financial_bf_ramt = models.CharField(db_column='Financial_Bf_Ramt', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    financial_crt_dt = models.DateTimeField(db_column='Financial_Crt_Dt', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Financial_Sheet'
        unique_together = (('financial_fy', 'financial_fy_dt', 'user_id', 'financial_gb', 'financial_serno'),)


class FinancialTrdstEcnt(models.Model):
    seq = models.IntegerField()
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    trdcd_semu = models.CharField(db_column='TrdCd_Semu', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    trdnm_semu = models.CharField(db_column='TrdNm_Semu', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    trdcd_ecnt = models.CharField(db_column='TrdCd_Ecnt', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    trdnm_ecnt = models.CharField(db_column='TrdNm_Ecnt', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    trdst_num = models.CharField(db_column='Trdst_Num', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    trdst_cmt = models.CharField(db_column='Trdst_Cmt', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Financial_Trdst_Ecnt'



class IncometaxDeduct(models.Model):
    yy = models.CharField(db_column='YY', primary_key=True, max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tax_deductgb = models.CharField(db_column='Tax_DeductGb', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tax_deduct_min = models.DecimalField(db_column='Tax_Deduct_Min', max_digits=13, decimal_places=0)  # Field name made lowercase.
    tax_deduct_max = models.DecimalField(db_column='Tax_Deduct_Max', max_digits=13, decimal_places=0)  # Field name made lowercase.
    taxrat = models.DecimalField(db_column='TaxRat', max_digits=9, decimal_places=4)  # Field name made lowercase.
    tax_deduct_amt = models.DecimalField(db_column='Tax_Deduct_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    mdfy_dt = models.CharField(db_column='Mdfy_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'IncomeTax_Deduct'
        unique_together = (('yy', 'tax_deductgb', 'tax_deduct_min', 'tax_deduct_max'),)


class IncometaxReport(models.Model):
    yy = models.CharField(db_column='YY', primary_key=True, max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_no = models.CharField(db_column='Ibo_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_type = models.CharField(db_column='Ibo_Type', max_length=7, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_name = models.CharField(db_column='Ibo_Name', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_addr = models.CharField(db_column='Ibo_Addr', max_length=200, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tax_reportty = models.CharField(db_column='Tax_ReportTy', max_length=7, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tax_reportgb = models.CharField(db_column='Tax_ReportGB', max_length=7, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    book_chkyn = models.CharField(db_column='Book_ChkYN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    report_gb = models.CharField(db_column='Report_GB', max_length=7, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    seq_no = models.CharField(db_column='Seq_No', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    income_totamt = models.DecimalField(db_column='Income_TotAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    expenses_amt = models.DecimalField(db_column='Expenses_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    global_incometax = models.DecimalField(db_column='Global_IncomeTax', max_digits=13, decimal_places=0)  # Field name made lowercase.
    onesf_ddct = models.DecimalField(db_column='Onesf_ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    spos_yn = models.CharField(db_column='Spos_yn', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    spos_ddct_yn = models.CharField(db_column='Spos_ddct_yn', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    spos_ddct = models.DecimalField(db_column='Spos_ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    support_fmly_cnt = models.IntegerField(db_column='Support_fmly_cnt')  # Field name made lowercase.
    support_fmly_ddct = models.DecimalField(db_column='Support_fmly_ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    path_prime_cnt = models.IntegerField(db_column='Path_prime_cnt')  # Field name made lowercase.
    path_prime_cnt2 = models.IntegerField(db_column='Path_prime_cnt2')  # Field name made lowercase.
    path_prime_ddct = models.DecimalField(db_column='Path_prime_ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    hcpsn_cnt = models.IntegerField(db_column='Hcpsn_cnt')  # Field name made lowercase.
    hcpsn_ddct = models.DecimalField(db_column='Hcpsn_ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    wman_ddct_yn = models.CharField(db_column='Wman_ddct_yn', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    wman_ddct = models.DecimalField(db_column='Wman_ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    chd_cnt = models.IntegerField(db_column='Chd_cnt')  # Field name made lowercase.
    chd_ddct = models.DecimalField(db_column='Chd_ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    minty_add_ddct = models.DecimalField(db_column='Minty_add_ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    annu_work_amt = models.DecimalField(db_column='Annu_Work_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    annu_etc_amt = models.DecimalField(db_column='Annu_Etc_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    med_insur_amt = models.DecimalField(db_column='Med_insur_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    emply_insu_amt = models.DecimalField(db_column='Emply_insu_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    hcpsn_insu_amt = models.DecimalField(db_column='Hcpsn_insu_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    etc_insu_amt = models.DecimalField(db_column='Etc_insu_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    insu_ddct = models.DecimalField(db_column='Insu_ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    self_med_amt = models.DecimalField(db_column='Self_med_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    self_med_ddct = models.DecimalField(db_column='Self_med_Ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    selfopt_med_cnt = models.DecimalField(db_column='SelfOpt_med_Cnt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    selfopt_med_amt = models.DecimalField(db_column='SelfOpt_med_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    selfopt_med_ddct = models.DecimalField(db_column='SelfOpt_med_Ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    other_med_amt = models.DecimalField(db_column='Other_med_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    other_med_ddct = models.DecimalField(db_column='Other_med_Ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    otheropt_med_cnt = models.DecimalField(db_column='OtherOpt_med_Cnt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    otheropt_med_amt = models.DecimalField(db_column='OtherOpt_med_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    otheropt_med_ddct = models.DecimalField(db_column='OtherOpt_med_Ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    med_ddct = models.DecimalField(db_column='Med_ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    onesf_schexps_amt = models.DecimalField(db_column='Onesf_Schexps_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    fmly_schexps_cnt = models.IntegerField(db_column='Fmly_Schexps_Cnt')  # Field name made lowercase.
    fmly_schexps_amt = models.DecimalField(db_column='Fmly_Schexps_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    unvs_schexps_cnt = models.IntegerField(db_column='Unvs_Schexps_Cnt')  # Field name made lowercase.
    unvs_schexps_amt = models.DecimalField(db_column='Unvs_Schexps_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    hcpsn_schexps_amt = models.DecimalField(db_column='Hcpsn_Schexps_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    schexps_ddct = models.DecimalField(db_column='Schexps_ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    housefund_amt = models.DecimalField(db_column='Housefund_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    housefundrepay_amt = models.DecimalField(db_column='Housefundrepay_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    houselongfund_intramt = models.DecimalField(db_column='Houselongfund_intrAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    house_fund_ddct = models.DecimalField(db_column='House_fund_ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    law_ctbt_amt = models.DecimalField(db_column='Law_ctbt_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    sch_ctbt_amt = models.DecimalField(db_column='Sch_ctbt_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    asgn_ctbt_amt = models.DecimalField(db_column='Asgn_ctbt_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    polit_ddct_amt = models.DecimalField(db_column='Polit_ddct_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    ctbt_ddct = models.DecimalField(db_column='Ctbt_ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    marry_cnt = models.IntegerField(db_column='Marry_Cnt')  # Field name made lowercase.
    move_cnt = models.IntegerField(db_column='Move_Cnt')  # Field name made lowercase.
    funeral_cnt = models.IntegerField(db_column='Funeral_Cnt')  # Field name made lowercase.
    mmf_ddct = models.DecimalField(db_column='MMF_ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    stand_ddct_tot = models.DecimalField(db_column='Stand_ddct_tot', max_digits=13, decimal_places=0)  # Field name made lowercase.
    spcl_ddct_tot = models.DecimalField(db_column='Spcl_ddct_tot', max_digits=13, decimal_places=0)  # Field name made lowercase.
    crdt_card_amt = models.DecimalField(db_column='Crdt_card_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    imt_card_amt = models.DecimalField(db_column='Imt_card_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    crdt_card_ddct = models.DecimalField(db_column='Crdt_card_ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    mix_ivst_amt = models.DecimalField(db_column='Mix_ivst_amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    mix_ivst_ddct = models.DecimalField(db_column='Mix_ivst_ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    indv_annu_pymt_amt = models.DecimalField(db_column='Indv_annu_pymt_amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    indv_annu_ddct = models.DecimalField(db_column='Indv_annu_ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    ansave_pymt_amt = models.DecimalField(db_column='Ansave_pymt_amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    ansave_ddct = models.DecimalField(db_column='Ansave_ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    workstock_save_amt = models.DecimalField(db_column='WorkStock_Save_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    workstock_save_ddct = models.DecimalField(db_column='WorkStock_Save_ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    retire_amt = models.DecimalField(db_column='Retire_amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    retire_ddct = models.DecimalField(db_column='Retire_ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    income_deductamt = models.DecimalField(db_column='Income_DeductAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    taxat_stand_amt = models.DecimalField(db_column='Taxat_Stand_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    taxat_stand_rate = models.DecimalField(db_column='Taxat_Stand_Rate', max_digits=13, decimal_places=0)  # Field name made lowercase.
    prct_tax = models.DecimalField(db_column='Prct_Tax', max_digits=13, decimal_places=0)  # Field name made lowercase.
    tax_reduct = models.DecimalField(db_column='Tax_Reduct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    book_incm_tax_ddct = models.DecimalField(db_column='Book_Incm_Tax_Ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    report_tax_ddct = models.DecimalField(db_column='Report_Tax_Ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    polc_ddct = models.DecimalField(db_column='Polc_Ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    housefundintr_amt = models.DecimalField(db_column='HouseFundIntr_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    housefundintr_ddct = models.DecimalField(db_column='HouseFundIntr_Ddct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    tax_deduct_amt = models.DecimalField(db_column='Tax_Deduct_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    fix_taxamt = models.DecimalField(db_column='Fix_TaxAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    add_taxamt = models.DecimalField(db_column='Add_TaxAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    add_tax_nobook = models.DecimalField(db_column='Add_Tax_NoBook', max_digits=13, decimal_places=0)  # Field name made lowercase.
    add_tax_noreturn = models.DecimalField(db_column='Add_Tax_NoReturn', max_digits=13, decimal_places=0)  # Field name made lowercase.
    addpay_taxamt = models.DecimalField(db_column='AddPay_TaxAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    interim_paytaxamt = models.DecimalField(db_column='Interim_PayTaxAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    bf_intax = models.DecimalField(db_column='Bf_Intax', max_digits=13, decimal_places=0)  # Field name made lowercase.
    bf_rsdtax = models.DecimalField(db_column='Bf_Rsdtax', max_digits=13, decimal_places=0)  # Field name made lowercase.
    bf_fmtax = models.DecimalField(db_column='Bf_Fmtax', max_digits=13, decimal_places=0)  # Field name made lowercase.
    fix_intax = models.DecimalField(db_column='Fix_Intax', max_digits=13, decimal_places=0)  # Field name made lowercase.
    fix_rsdtax = models.DecimalField(db_column='Fix_Rsdtax', max_digits=13, decimal_places=0)  # Field name made lowercase.
    install_paytax = models.DecimalField(db_column='Install_PayTax', max_digits=13, decimal_places=0)  # Field name made lowercase.
    trnfer_acno = models.CharField(db_column='Trnfer_Acno', max_length=25, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trnfer_bnknm = models.CharField(db_column='Trnfer_BnkNm', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    income_flowpg = models.CharField(db_column='Income_FlowPg', max_length=30, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    report_mthd = models.CharField(db_column='Report_Mthd', max_length=7, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    report_fixyn = models.CharField(db_column='Report_FixYN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    report_fixdate = models.CharField(db_column='Report_FixDate', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    report_docno = models.CharField(db_column='Report_DocNo', max_length=30, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    report_filenm = models.CharField(db_column='Report_FileNm', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    nts_reportfilenm = models.CharField(db_column='Nts_ReportFileNm', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    mdfy_dt = models.CharField(db_column='Mdfy_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    empowner_amt = models.DecimalField(db_column='EmpOwner_Amt', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    empowner_ddct_amt = models.DecimalField(db_column='EmpOwner_Ddct_Amt', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    add_ddctuse_amt_1 = models.DecimalField(db_column='Add_DdctUse_Amt_1', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    add_ddctuse_amt_2 = models.DecimalField(db_column='Add_DdctUse_Amt_2', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    chd_tax_ddct = models.DecimalField(db_column='Chd_Tax_Ddct', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    ansave_tax_ddct = models.DecimalField(db_column='Ansave_Tax_Ddct', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    insu_tax_ddct = models.DecimalField(db_column='Insu_Tax_Ddct', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    med_tax_ddct = models.DecimalField(db_column='Med_Tax_Ddct', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    schexps_tax_ddct = models.DecimalField(db_column='Schexps_Tax_Ddct', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    ctbt_tax_ddct = models.DecimalField(db_column='Ctbt_Tax_Ddct', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    houserent_tax_ddct = models.DecimalField(db_column='HouseRent_Tax_Ddct', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    spcl_tax_ddct_tot = models.DecimalField(db_column='Spcl_Tax_Ddct_tot', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    stnd_tax_ddct = models.DecimalField(db_column='Stnd_Tax_Ddct', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'IncomeTax_Report'
        unique_together = (('yy', 'ibo_no', 'seq_no'),)


class IncomeDeficit(models.Model):
    yy = models.CharField(db_column='YY', primary_key=True, max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_no = models.CharField(db_column='Ibo_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    incomegb = models.CharField(db_column='IncomeGb', max_length=7, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    incomeamt = models.DecimalField(db_column='IncomeAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    deficitedamt = models.DecimalField(db_column='DeficitedAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    deferdeficitedamt_40 = models.DecimalField(db_column='DeferDeficitedAmt_40', max_digits=13, decimal_places=0)  # Field name made lowercase.
    deferdeficitedamt_30 = models.DecimalField(db_column='DeferDeficitedAmt_30', max_digits=13, decimal_places=0)  # Field name made lowercase.
    incomeamtresidue = models.DecimalField(db_column='IncomeAmtResidue', max_digits=13, decimal_places=0)  # Field name made lowercase.
    transferyy = models.CharField(db_column='TransferYY', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    transferamt = models.DecimalField(db_column='TransferAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    transferbfexpamt = models.DecimalField(db_column='TransferBfExpAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    transferafexpamt = models.DecimalField(db_column='TransferAfExpAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    transferresidueamt = models.DecimalField(db_column='TransferResidueAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    mdfy_dt = models.CharField(db_column='Mdfy_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Income_Deficit'
        unique_together = (('yy', 'ibo_no', 'incomegb'),)


class IncomeExpense(models.Model):
    yy = models.CharField(db_column='YY', primary_key=True, max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_no = models.CharField(db_column='Ibo_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    income_gb = models.CharField(db_column='Income_Gb', max_length=2, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    income_seqno = models.CharField(db_column='Income_SeqNo', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    purchase1 = models.DecimalField(db_column='Purchase1', max_digits=13, decimal_places=0)  # Field name made lowercase.
    purchase2 = models.DecimalField(db_column='Purchase2', max_digits=13, decimal_places=0)  # Field name made lowercase.
    purchase3 = models.DecimalField(db_column='Purchase3', max_digits=13, decimal_places=0)  # Field name made lowercase.
    purchase4 = models.DecimalField(db_column='Purchase4', max_digits=13, decimal_places=0)  # Field name made lowercase.
    lentamt_1 = models.DecimalField(db_column='LentAmt_1', max_digits=13, decimal_places=0)  # Field name made lowercase.
    lentamt_2 = models.DecimalField(db_column='LentAmt_2', max_digits=13, decimal_places=0)  # Field name made lowercase.
    lentamt_3 = models.DecimalField(db_column='LentAmt_3', max_digits=13, decimal_places=0)  # Field name made lowercase.
    lentamt_4 = models.DecimalField(db_column='LentAmt_4', max_digits=13, decimal_places=0)  # Field name made lowercase.
    laboramt1 = models.DecimalField(db_column='LaborAmt1', max_digits=13, decimal_places=0)  # Field name made lowercase.
    laboramt2 = models.DecimalField(db_column='LaborAmt2', max_digits=13, decimal_places=0)  # Field name made lowercase.
    laboramt3 = models.DecimalField(db_column='LaborAmt3', max_digits=13, decimal_places=0)  # Field name made lowercase.
    laboramt4 = models.DecimalField(db_column='LaborAmt4', max_digits=13, decimal_places=0)  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    mdfy_dt = models.CharField(db_column='Mdfy_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Income_Expense'
        unique_together = (('yy', 'ibo_no', 'income_gb', 'income_seqno'),)


class IncomeExpenseMainreceit(models.Model):
    yy = models.CharField(db_column='YY', primary_key=True, max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    seq_no = models.CharField(db_column='Seq_No', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_no = models.CharField(db_column='Ibo_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    income_gb = models.CharField(db_column='Income_Gb', max_length=2, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    income_seqno = models.CharField(db_column='Income_SeqNo', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    comname = models.CharField(db_column='ComName', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    comber = models.CharField(db_column='ComBer', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ownname = models.CharField(db_column='OwnName', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ownssn = models.CharField(db_column='OwnSsn', max_length=13, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    deal_gb = models.CharField(db_column='Deal_Gb', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    deal_cnt = models.DecimalField(db_column='Deal_Cnt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    deal_amt = models.DecimalField(db_column='Deal_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    mdfy_dt = models.CharField(db_column='Mdfy_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Income_Expense_MainReceit'
        unique_together = (('yy', 'ibo_no', 'seq_no', 'income_seqno', 'income_gb'),)


class IncomeList(models.Model):
    yy = models.CharField(db_column='YY', primary_key=True, max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_no = models.CharField(db_column='Ibo_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    income_gb = models.CharField(db_column='Income_Gb', max_length=2, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    seq_no = models.CharField(db_column='Seq_No', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    reg_name = models.CharField(db_column='Reg_Name', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    reg_no = models.CharField(db_column='Reg_No', max_length=13, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    reg_addr = models.CharField(db_column='Reg_Addr', max_length=200, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    reg_preman = models.CharField(db_column='Reg_PreMan', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    reg_premanjumin = models.CharField(db_column='Reg_PreManJumin', max_length=13, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    jongmok = models.CharField(db_column='JongMok', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    uptae = models.CharField(db_column='UpTae', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    upjong_code = models.CharField(db_column='UpJong_Code', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    work_amt1 = models.DecimalField(db_column='Work_Amt1', max_digits=13, decimal_places=0)  # Field name made lowercase.
    work_amt2 = models.DecimalField(db_column='Work_Amt2', max_digits=13, decimal_places=0)  # Field name made lowercase.
    work_amt3 = models.DecimalField(db_column='Work_Amt3', max_digits=13, decimal_places=0)  # Field name made lowercase.
    work_amt4 = models.DecimalField(db_column='Work_Amt4', max_digits=13, decimal_places=0)  # Field name made lowercase.
    incometotamt = models.DecimalField(db_column='IncomeTotAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    simple_rate = models.DecimalField(db_column='Simple_Rate', max_digits=5, decimal_places=2)  # Field name made lowercase.
    simpleex_rate = models.DecimalField(db_column='SimpleEx_Rate', max_digits=5, decimal_places=2)  # Field name made lowercase.
    basic_rate = models.DecimalField(db_column='Basic_Rate', max_digits=5, decimal_places=2)  # Field name made lowercase.
    bfexpense = models.DecimalField(db_column='BfExpense', max_digits=13, decimal_places=0)  # Field name made lowercase.
    nowexpense = models.DecimalField(db_column='NowExpense', max_digits=13, decimal_places=0)  # Field name made lowercase.
    afexpense = models.DecimalField(db_column='AfExpense', max_digits=13, decimal_places=0)  # Field name made lowercase.
    expense_amt = models.DecimalField(db_column='Expense_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    needexpense = models.DecimalField(db_column='NeedExpense', max_digits=13, decimal_places=0)  # Field name made lowercase.
    standincomeamt = models.DecimalField(db_column='StandIncomeAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    simple_rateamt = models.DecimalField(db_column='Simple_RateAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    basic_rateamt = models.DecimalField(db_column='Basic_RateAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    compincomeamt = models.DecimalField(db_column='CompIncomeAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    expense_real_book = models.DecimalField(db_column='Expense_Real_Book', max_digits=13, decimal_places=0)  # Field name made lowercase.
    expense_real_simple = models.DecimalField(db_column='Expense_Real_Simple', max_digits=13, decimal_places=0)  # Field name made lowercase.
    expense_real_basic = models.DecimalField(db_column='Expense_Real_Basic', max_digits=13, decimal_places=0)  # Field name made lowercase.
    handicapchk = models.CharField(db_column='HandicapChk', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    handi_simplerate = models.DecimalField(db_column='Handi_SimpleRate', max_digits=6, decimal_places=2)  # Field name made lowercase.
    handi_simplerate_add = models.DecimalField(db_column='Handi_SimpleRate_Add', max_digits=6, decimal_places=2)  # Field name made lowercase.
    handi_simpleexpense = models.DecimalField(db_column='Handi_SimpleExpense', max_digits=13, decimal_places=0)  # Field name made lowercase.
    incomeamtfix_book = models.DecimalField(db_column='IncomeAmtFix_Book', max_digits=13, decimal_places=0)  # Field name made lowercase.
    incomeamtfix_simple = models.DecimalField(db_column='IncomeAmtFix_Simple', max_digits=13, decimal_places=0)  # Field name made lowercase.
    incomeamtfix_basic = models.DecimalField(db_column='IncomeAmtFix_Basic', max_digits=13, decimal_places=0)  # Field name made lowercase.
    incomeamtfix_soho = models.DecimalField(db_column='IncomeAmtFix_SoHo', max_digits=13, decimal_places=0)  # Field name made lowercase.
    withholdreg_name = models.CharField(db_column='WithHoldReg_Name', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    withholdreg_no = models.CharField(db_column='WithHoldReg_No', max_length=13, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    intaxamt1 = models.DecimalField(db_column='IntaxAmt1', max_digits=13, decimal_places=0)  # Field name made lowercase.
    intaxamt2 = models.DecimalField(db_column='IntaxAmt2', max_digits=13, decimal_places=0)  # Field name made lowercase.
    intaxamt3 = models.DecimalField(db_column='IntaxAmt3', max_digits=13, decimal_places=0)  # Field name made lowercase.
    intaxamt4 = models.DecimalField(db_column='IntaxAmt4', max_digits=13, decimal_places=0)  # Field name made lowercase.
    intaxamt1_1 = models.DecimalField(db_column='IntaxAmt1_1', max_digits=13, decimal_places=0)  # Field name made lowercase.
    intaxamt2_1 = models.DecimalField(db_column='IntaxAmt2_1', max_digits=13, decimal_places=0)  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    mdfy_dt = models.CharField(db_column='Mdfy_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Income_List'
        unique_together = (('yy', 'ibo_no', 'income_gb', 'seq_no'),)


class IncomeMasterplan(models.Model):
    creyy = models.CharField(db_column='CreYY', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_no = models.CharField(db_column='Ibo_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    business_num = models.CharField(db_column='Business_Num', max_length=12, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    business_name = models.CharField(db_column='Business_Name', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    business_addr = models.CharField(db_column='Business_Addr', max_length=200, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    a0000 = models.DecimalField(db_column='A0000', max_digits=13, decimal_places=0)  # Field name made lowercase.
    a0001 = models.DecimalField(db_column='A0001', max_digits=13, decimal_places=0)  # Field name made lowercase.
    b0000 = models.DecimalField(db_column='B0000', max_digits=13, decimal_places=0)  # Field name made lowercase.
    c0001 = models.DecimalField(db_column='C0001', max_digits=13, decimal_places=0)  # Field name made lowercase.
    c0002 = models.DecimalField(db_column='C0002', max_digits=13, decimal_places=0)  # Field name made lowercase.
    c0003 = models.DecimalField(db_column='C0003', max_digits=13, decimal_places=0)  # Field name made lowercase.
    c0004 = models.DecimalField(db_column='C0004', max_digits=13, decimal_places=0)  # Field name made lowercase.
    e0001 = models.DecimalField(db_column='E0001', max_digits=13, decimal_places=0)  # Field name made lowercase.
    f0001 = models.DecimalField(db_column='F0001', max_digits=13, decimal_places=0)  # Field name made lowercase.
    g0001 = models.DecimalField(db_column='G0001', max_digits=13, decimal_places=0)  # Field name made lowercase.
    h0001 = models.DecimalField(db_column='H0001', max_digits=13, decimal_places=0)  # Field name made lowercase.
    i0001 = models.DecimalField(db_column='I0001', max_digits=13, decimal_places=0)  # Field name made lowercase.
    j0001 = models.DecimalField(db_column='J0001', max_digits=13, decimal_places=0)  # Field name made lowercase.
    s0000 = models.DecimalField(db_column='S0000', max_digits=13, decimal_places=0)  # Field name made lowercase.
    t0000 = models.DecimalField(db_column='T0000', max_digits=13, decimal_places=0)  # Field name made lowercase.
    u0000 = models.DecimalField(db_column='U0000', max_digits=13, decimal_places=0)  # Field name made lowercase.
    v0000 = models.DecimalField(max_digits=13, decimal_places=0)
    contribution_plus = models.DecimalField(db_column='Contribution_Plus', max_digits=13, decimal_places=0)  # Field name made lowercase.
    contribution_minus = models.DecimalField(db_column='Contribution_Minus', max_digits=13, decimal_places=0)  # Field name made lowercase.
    income_book = models.DecimalField(db_column='Income_Book', max_digits=13, decimal_places=0)  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    mdfy_dt = models.CharField(db_column='Mdfy_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Income_MasterPlan'


class IncomeSuppfmly(models.Model):
    yy = models.CharField(db_column='YY', primary_key=True, max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_no = models.CharField(db_column='Ibo_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    seq_no = models.CharField(db_column='Seq_No', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    fmly_gb = models.CharField(db_column='Fmly_GB', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    fmly_nm = models.CharField(db_column='Fmly_Nm', max_length=15, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    fmly_residno = models.CharField(db_column='Fmly_ResidNo', max_length=13, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    fmly_addr = models.CharField(db_column='Fmly_Addr', max_length=200, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    etc_incomeamt = models.DecimalField(db_column='Etc_IncomeAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    st_ded_yn = models.CharField(db_column='ST_Ded_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    older_ded_yn_1 = models.CharField(db_column='Older_Ded_YN_1', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    older_ded_yn_2 = models.CharField(db_column='Older_Ded_YN_2', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    handi_ded_yn = models.CharField(db_column='Handi_Ded_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    fem_ded_yn = models.CharField(db_column='Fem_Ded_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    rear_ded_yn = models.CharField(db_column='Rear_Ded_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    insur_ded_yn = models.CharField(db_column='Insur_Ded_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    med_ded_yn = models.CharField(db_column='Med_Ded_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    sch_ded_yn = models.CharField(db_column='Sch_Ded_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    cre_ded_yn = models.CharField(db_column='Cre_Ded_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    mdfy_dt = models.CharField(db_column='Mdfy_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Income_SuppFmly'
        unique_together = (('yy', 'ibo_no', 'seq_no', 'fmly_residno'),)


class MemAdmin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='Mem_Admin', null=True)
    seq_no = models.AutoField(db_column='Seq_No',primary_key=True)  # Field name made lowercase.
    admin_id = models.CharField(db_column='Admin_ID', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    admin_pwd = models.CharField(db_column='Admin_Pwd', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    admin_name = models.CharField(db_column='Admin_Name', max_length=30, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    admin_tel_no = models.CharField(db_column='Admin_Tel_No', max_length=14, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    admin_hp_no = models.CharField(db_column='Admin_Hp_No', max_length=14, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    admin_email = models.CharField(db_column='Admin_Email', max_length=60, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    admin_biz_area = models.CharField(db_column='Admin_Biz_Area', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    manage_YN = models.CharField(db_column='manage_YN', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_level = models.CharField(db_column='Biz_Level', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    grade = models.CharField(db_column='Grade', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    reg_date = models.DateTimeField(db_column='Reg_Date')  # Field name made lowercase.
    up_date = models.DateTimeField(db_column='Up_Date', blank=True, null=True)  # Field name made lowercase.
    log_date = models.DateTimeField(db_column='Log_Date', blank=True, null=True)  # Field name made lowercase.
    del_yn = models.CharField(db_column='Del_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    del_date = models.DateTimeField(db_column='Del_Date', blank=True, null=True)  # Field name made lowercase.
    del_reason = models.CharField(db_column='Del_Reason', max_length=60, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    htx_id = models.CharField(db_column='Htx_ID', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    class Meta:
        managed = False
        db_table = 'Mem_Admin'




class MemDeal(models.Model):
    seq_no = models.CharField(primary_key=True, max_length=10, db_collation='Korean_Wansung_CI_AS')
    biz_manager = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS')
    kijang_yn = models.CharField(db_column='kijang_YN', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    keeping_yn = models.CharField(db_column='keeping_YN', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    cms_yn = models.CharField(db_column='cms_YN', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    tel_sincasale = models.CharField(db_column='Tel_sincaSale', max_length=500, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    goyoung_jungkyu = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    goyoung_ilyoung = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    goyoung_sayoup = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    goyoung_banki = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    ediid = models.CharField(db_column='EDIID', max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    edipw = models.CharField(db_column='EDIPW', max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    taxsaveid = models.CharField(db_column='TaxsaveID', max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    taxsavepw = models.CharField(db_column='TaxsavePW', max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    hometaxid = models.CharField(db_column='HometaxID', max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    hometaxpw = models.CharField(db_column='HometaxPW', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    hometaxagree = models.CharField(db_column='hometaxAgree', max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    taxmgr_name = models.CharField(db_column='taxMgr_Name', max_length=7, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    taxmgr_tel = models.CharField(db_column='taxMgr_Tel', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    taxmgr_fax = models.CharField(db_column='taxMgr_Fax', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    createddate = models.DateTimeField(db_column='CreatedDate', blank=True, null=True)  # Field name made lowercase.
    feeamt = models.DecimalField(db_column='FeeAmt', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    taltyoedate = models.CharField(db_column='taltyoeDate', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    taltyoereason = models.CharField(db_column='taltyoeReason', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    fiscalmm = models.CharField(db_column='FiscalMM', max_length=2, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    sanjaerate = models.CharField(db_column='SanJaeRate', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Mem_Deal'





class MemUser(models.Model):
    seq_no = models.CharField(db_column='Seq_No', primary_key=True, max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    duzon_id = models.CharField(db_column='Duzon_ID', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    user_id = models.CharField(db_column='User_ID', max_length=12, db_collation='Korean_Wansung_CS_AS')  # Field name made lowercase.
    user_pwd = models.CharField(db_column='User_Pwd', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    name = models.CharField(db_column='Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ssn = models.CharField(db_column='Ssn', max_length=13, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    email = models.CharField(db_column='Email', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    zipcode = models.CharField(db_column='Zipcode', max_length=7, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    addr1 = models.CharField(db_column='Addr1', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    addr2 = models.CharField(db_column='Addr2', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tel_no = models.CharField(db_column='Tel_No', max_length=14, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    hp_no = models.CharField(db_column='Hp_No', max_length=14, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    taxation_no = models.CharField(db_column='Taxation_No', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_image = models.CharField(db_column='Biz_Image', max_length=500, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    taxoffice_code = models.CharField(db_column='TaxOffice_Code', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    taxbank_acc = models.CharField(db_column='TaxBank_Acc', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ward_off = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS')
    biz_par_chk = models.CharField(db_column='Biz_Par_Chk', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_par_ms = models.CharField(db_column='Biz_Par_MS', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_par_rate = models.IntegerField(db_column='Biz_Par_Rate')  # Field name made lowercase.
    biz_par_ssn = models.CharField(db_column='Biz_Par_Ssn', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_type = models.IntegerField(db_column='Biz_Type')  # Field name made lowercase.
    upjong = models.IntegerField(db_column='Upjong')  # Field name made lowercase.
    biz_no = models.CharField(db_column='Biz_No', max_length=12, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_name = models.CharField(db_column='Biz_Name', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ceo_name = models.CharField(db_column='Ceo_Name', max_length=30, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    uptae = models.CharField(db_column='Uptae', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    jongmok = models.CharField(db_column='Jongmok', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_zipcode = models.CharField(db_column='Biz_Zipcode', max_length=7, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_addr1 = models.CharField(db_column='Biz_Addr1', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_addr2 = models.CharField(db_column='Biz_Addr2', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_tel = models.CharField(db_column='Biz_Tel', max_length=14, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_fax = models.CharField(db_column='Biz_Fax', max_length=14, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    isrnd = models.CharField(db_column='isRND', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    saletimail = models.CharField(db_column='SaleTIMail', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    saletiname = models.CharField(db_column='SaleTIName', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    isventure = models.CharField(db_column='isVENTURE', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    biz_start_day = models.CharField(db_column='Biz_Start_Day', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_end_day = models.CharField(db_column='Biz_End_Day', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_end_reason = models.CharField(db_column='Biz_End_Reason', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ret_bank_code = models.CharField(db_column='Ret_Bank_Code', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ret_bank_name = models.CharField(db_column='Ret_Bank_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ret_account = models.CharField(db_column='Ret_Account', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    reg_date = models.DateTimeField(db_column='Reg_Date', blank=True, null=True)  # Field name made lowercase.
    up_date = models.DateTimeField(db_column='Up_Date', blank=True, null=True)  # Field name made lowercase.
    log_date = models.DateTimeField(db_column='Log_Date', blank=True, null=True)  # Field name made lowercase.
    dk_manage = models.CharField(db_column='DK_manage', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    del_yn = models.CharField(db_column='Del_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    del_date = models.DateTimeField(db_column='Del_Date')  # Field name made lowercase.
    del_reason = models.CharField(db_column='Del_Reason', max_length=60, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    pay_month = models.DecimalField(db_column='Pay_Month', max_digits=9, decimal_places=0)  # Field name made lowercase.
    pay_year = models.DecimalField(db_column='Pay_Year', max_digits=9, decimal_places=0)  # Field name made lowercase.
    pay_not = models.DecimalField(db_column='Pay_Not', max_digits=9, decimal_places=0)  # Field name made lowercase.
    sale_confirm = models.CharField(db_column='Sale_Confirm', max_length=14, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    etc = models.CharField(db_column='ETC', max_length=1000, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    open_date = models.CharField(max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    close_date = models.CharField(max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    close_resn = models.CharField(max_length=200, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    join_yn = models.CharField(db_column='Join_YN', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    uptaecd = models.CharField(db_column='UptaeCd', max_length=6, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    biz_area = models.CharField(db_column='Biz_Area', max_length=30, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Mem_User'
        unique_together = (('seq_no', 'user_id'),)


class MemUsers(models.Model):
    seq_no = models.AutoField(db_column='Seq_No',primary_key=True)  # Field name made lowercase.
    biz_code = models.CharField(db_column='Biz_Code', max_length=12, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_no = models.CharField(db_column='Ibo_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_type = models.CharField(db_column='Ibo_Type', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_type_std = models.CharField(db_column='Ibo_Type_Std', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_type_chg = models.CharField(db_column='Ibo_Type_Chg', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    user_id = models.CharField(db_column='User_ID', max_length=12, db_collation='Korean_Wansung_CS_AS')  # Field name made lowercase.
    user_pwd = models.CharField(db_column='User_Pwd', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    name = models.CharField(db_column='Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ssn = models.CharField(db_column='Ssn', max_length=13, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    email = models.CharField(db_column='Email', max_length=60, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    zipcode = models.CharField(db_column='Zipcode', max_length=7, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    addr1 = models.CharField(db_column='Addr1', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    addr2 = models.CharField(db_column='Addr2', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tel_no = models.CharField(db_column='Tel_No', max_length=14, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    hp_no = models.CharField(db_column='Hp_No', max_length=14, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    taxation_no = models.CharField(db_column='Taxation_No', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    taxation = models.CharField(db_column='Taxation', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    taxoffice_code = models.CharField(db_column='TaxOffice_Code', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    taxbank_acc = models.CharField(db_column='TaxBank_Acc', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ward_off = models.CharField(db_column='Ward_Off', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_par_chk = models.CharField(db_column='Biz_Par_Chk', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_par_ms = models.CharField(db_column='Biz_Par_MS', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_par_rate = models.IntegerField(db_column='Biz_Par_Rate')  # Field name made lowercase.
    biz_par_ssn = models.CharField(db_column='Biz_Par_Ssn', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_type = models.IntegerField(db_column='Biz_Type')  # Field name made lowercase.
    upjong = models.IntegerField(db_column='Upjong')  # Field name made lowercase.
    biz_no = models.CharField(db_column='Biz_No', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_name = models.CharField(db_column='Biz_Name', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ceo_name = models.CharField(db_column='Ceo_Name', max_length=30, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    uptae = models.CharField(db_column='Uptae', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    jongmok = models.CharField(db_column='Jongmok', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_zipcode = models.CharField(db_column='Biz_Zipcode', max_length=7, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_addr1 = models.CharField(db_column='Biz_Addr1', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_addr2 = models.CharField(db_column='Biz_Addr2', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_tel = models.CharField(db_column='Biz_Tel', max_length=14, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_fax = models.CharField(db_column='Biz_Fax', max_length=14, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_taxation = models.CharField(db_column='Biz_Taxation', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_taxoffice_code = models.CharField(db_column='Biz_TaxOffice_Code', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_taxbank_acc = models.CharField(db_column='Biz_TaxBank_Acc', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_ward_off = models.CharField(db_column='Biz_Ward_Off', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_start_day = models.CharField(db_column='Biz_Start_Day', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_end_day = models.CharField(db_column='Biz_End_Day', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_end_reason = models.CharField(db_column='Biz_End_Reason', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ret_bank_code = models.CharField(db_column='Ret_Bank_Code', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ret_bank_name = models.CharField(db_column='Ret_Bank_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ret_account = models.CharField(db_column='Ret_Account', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    bat_date = models.DateTimeField(db_column='Bat_Date')  # Field name made lowercase.
    reg_date = models.DateTimeField(db_column='Reg_Date', blank=True, null=True)  # Field name made lowercase.
    up_date = models.DateTimeField(db_column='Up_Date', blank=True, null=True)  # Field name made lowercase.
    log_date = models.DateTimeField(db_column='Log_Date', blank=True, null=True)  # Field name made lowercase.
    vat_date = models.CharField(db_column='Vat_Date', max_length=7, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    del_yn = models.CharField(db_column='Del_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    del_date = models.DateTimeField(db_column='Del_Date', blank=True, null=True)  # Field name made lowercase.
    del_reason = models.CharField(db_column='Del_Reason', max_length=60, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    old_data = models.CharField(db_column='Old_Data', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    amw_chk = models.CharField(db_column='AMW_chk', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    test_id = models.CharField(db_column='Test_ID', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Mem_Users'


class OfstAdmin(models.Model):
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    ofst_bizno = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    ofst_addr1 = models.CharField(max_length=200, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    ofst_addr2 = models.CharField(max_length=200, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    ofst_id = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    ofst_name = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    ofst_date = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    ofst_fee = models.DecimalField(db_column='ofst_Fee', max_digits=18, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    ofst_mng_name = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    ofst_mng_tel = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    ofst_mng_email = models.CharField(max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    ti_mng_name = models.CharField(db_column='TI_mng_name', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    ti_mng_tel = models.CharField(db_column='TI_mng_tel', max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    ti_mng_fax = models.CharField(db_column='TI_mng_fax', max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    ti_mng_email = models.CharField(db_column='TI_mng_email', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    pay_amt_1 = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    pay_amt_2 = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    pay_amt_3 = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    pay_amt_4 = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    pay_amt_5 = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    pay_amt_6 = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    pay_amt_7 = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    pay_amt_8 = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    pay_amt_9 = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    pay_amt_10 = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    pay_date_1 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    pay_date_2 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    pay_date_3 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    pay_date_4 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    pay_date_5 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    pay_date_6 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    pay_date_7 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    pay_date_8 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    pay_date_9 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    pay_date_10 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    keeping_yn = models.CharField(db_column='keeping_YN', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'OFST_admin'


class OfstUser(models.Model):
    seq_admin = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    seq_user = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    user_name = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    user_dong = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    user_ho = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    user_fee = models.DecimalField(db_column='user_Fee', max_digits=18, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    user_fee_yn = models.CharField(db_column='user_Fee_YN', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    reg_date = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    bd_price = models.DecimalField(db_column='BD_price', max_digits=18, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    biz_no = models.CharField(max_length=12, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    jumin = models.CharField(db_column='Jumin', max_length=14, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    user_hpno = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    user_email = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    bank_name = models.CharField(max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    bank_code = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    bank_num = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    cashbill_yn = models.CharField(db_column='cashbill_YN', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    cashbill_date = models.CharField(db_column='cashbill_Date', max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    partnership_yn = models.CharField(db_column='partnership_YN', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    partner_name = models.CharField(db_column='partner_Name', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    partner_ssn = models.CharField(max_length=14, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    enddate = models.CharField(db_column='endDate', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    bigo = models.TextField(db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    keeping_yn = models.CharField(db_column='keeping_YN', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'OFST_user'


class Refndamt(models.Model):
    refndamt = models.DecimalField(db_column='RefndAmt', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    notrefndamt = models.DecimalField(db_column='NotRefndAmt', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'RefndAmt'


class Tmp(models.Model):
    seq_no = models.CharField(db_column='Seq_No', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    work_yy = models.CharField(db_column='Work_YY', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='Acnt_cd', max_length=3, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_nm = models.CharField(db_column='Acnt_Nm', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_dt = models.CharField(db_column='Tran_Dt', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    remk = models.CharField(db_column='Remk', max_length=500, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_code = models.CharField(db_column='Trader_Code', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_name = models.CharField(db_column='Trader_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_bizno = models.CharField(db_column='Trader_Bizno', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    slip_no = models.CharField(db_column='Slip_No', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_stat = models.CharField(db_column='Tran_Stat', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crdr = models.CharField(db_column='CrDr', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tranamt_cr = models.DecimalField(db_column='TranAmt_Cr', max_digits=15, decimal_places=0)  # Field name made lowercase.
    tranamt_dr = models.DecimalField(db_column='TranAmt_Dr', max_digits=15, decimal_places=0)  # Field name made lowercase.
    employee_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    employee_name = models.CharField(db_column='employee_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    credit_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    credit_name = models.CharField(db_column='credit_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    place_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    place_name = models.CharField(db_column='place_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    project_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    project_name = models.CharField(db_column='project_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    cncl_dt = models.CharField(db_column='Cncl_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'TMP_사고'


class TaxfreeList(models.Model):
    yy = models.CharField(db_column='YY', primary_key=True, max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    user_id = models.CharField(db_column='User_ID', max_length=12, db_collation='Korean_Wansung_CS_AS')  # Field name made lowercase.
    incometotamt = models.DecimalField(db_column='IncomeTotAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    incomebillamt = models.DecimalField(db_column='IncomeBillAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    incometaxbillamt = models.DecimalField(db_column='IncomeTaxBillAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    incomecardamt = models.DecimalField(db_column='IncomeCardAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    incomecashamt = models.DecimalField(db_column='IncomeCashAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    incomegiroamt = models.DecimalField(db_column='IncomeGiroAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    incomebankamt = models.DecimalField(db_column='IncomeBankAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    incomeetcamt = models.DecimalField(db_column='IncomeEtcAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    buytotamt = models.DecimalField(db_column='BuyTotAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    buybillamt = models.DecimalField(db_column='BuyBillAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    buytaxbillamt = models.DecimalField(db_column='BuyTaxBillAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    buycardamt = models.DecimalField(db_column='BuyCardAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    buildingarea = models.DecimalField(db_column='BuildingArea', max_digits=13, decimal_places=0)  # Field name made lowercase.
    rentdeposit = models.DecimalField(db_column='RentDeposit', max_digits=13, decimal_places=0)  # Field name made lowercase.
    cars = models.DecimalField(db_column='Cars', max_digits=13, decimal_places=0)  # Field name made lowercase.
    etcequipment = models.DecimalField(db_column='EtcEquipment', max_digits=13, decimal_places=0)  # Field name made lowercase.
    employeecnt = models.DecimalField(db_column='EmployeeCnt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    basiccost = models.DecimalField(db_column='BasicCost', max_digits=13, decimal_places=0)  # Field name made lowercase.
    rentamt = models.DecimalField(db_column='RentAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    buyamt = models.DecimalField(db_column='BuyAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    payroll = models.DecimalField(db_column='PayRoll', max_digits=13, decimal_places=0)  # Field name made lowercase.
    etccost = models.DecimalField(db_column='EtcCost', max_digits=13, decimal_places=0)  # Field name made lowercase.
    attachpaper_1 = models.CharField(db_column='AttachPaper_1', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    attachpaper_2 = models.CharField(db_column='AttachPaper_2', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    attachpaper_3 = models.CharField(db_column='AttachPaper_3', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    attachpaper_4 = models.CharField(db_column='AttachPaper_4', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    mdfy_dt = models.CharField(db_column='Mdfy_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'TaxFree_List'
        unique_together = (('yy', 'user_id'),)


class TblAddrnoffice(models.Model):
    postnum1 = models.CharField(db_column='PostNum1', max_length=7, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    postnum2 = models.CharField(db_column='PostNum2', max_length=6, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    seq_num = models.CharField(db_column='Seq_Num', max_length=3, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    addr_sido = models.CharField(db_column='Addr_Sido', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    addr_sikunku = models.CharField(db_column='Addr_SiKunKu', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    addr_yupmeundong = models.CharField(db_column='Addr_YupMeunDong', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    addr_lee = models.CharField(db_column='Addr_Lee', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    addr_doseu = models.CharField(db_column='Addr_Doseu', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    addr_bunji = models.CharField(db_column='Addr_Bunji', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    apt = models.CharField(db_column='Apt', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    update_date = models.CharField(db_column='Update_Date', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    address = models.CharField(db_column='Address', max_length=200, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    office_code = models.CharField(db_column='Office_Code', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    taxoffice_code = models.CharField(db_column='TaxOffice_Code', max_length=3, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    taxoffice_name = models.CharField(db_column='TaxOffice_Name', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    bankacc = models.CharField(db_column='BankAcc', max_length=6, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_AddrNOffice'


class TblBank(models.Model):
    bank_cd = models.CharField(db_column='Bank_cd', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    bank_accname = models.CharField(db_column='Bank_AccName', max_length=30, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_Bank'


class TblBankaccdt(models.Model):
    seq_no = models.CharField(db_column='Seq_no', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    bank_cd = models.CharField(db_column='Bank_cd', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    bank_accnum = models.CharField(db_column='Bank_AccNum', max_length=30, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tid = models.CharField(max_length=32, db_collation='Korean_Wansung_CI_AS')
    trdate = models.CharField(max_length=8, db_collation='Korean_Wansung_CI_AS')
    trserial = models.IntegerField()
    trdt = models.CharField(max_length=14, db_collation='Korean_Wansung_CI_AS')
    accin = models.CharField(db_column='accIn', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    accout = models.CharField(db_column='accOut', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    balance = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS')
    remark1 = models.CharField(max_length=500, db_collation='Korean_Wansung_CI_AS')
    remark2 = models.CharField(max_length=500, db_collation='Korean_Wansung_CI_AS')
    remark3 = models.CharField(max_length=500, db_collation='Korean_Wansung_CI_AS')
    remark4 = models.CharField(max_length=500, db_collation='Korean_Wansung_CI_AS')
    regdt = models.CharField(db_column='regDT', max_length=14, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    memo = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    acc_yn = models.CharField(db_column='Acc_YN', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crt_dt = models.DateTimeField(db_column='Crt_Dt', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_BankAccDT'


class TblBankaccform(models.Model):
    seq_no = models.CharField(db_column='Seq_no', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    bank_cd = models.CharField(db_column='Bank_cd', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    bank_accnum = models.CharField(db_column='Bank_AccNum', max_length=30, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    bank_accnumpwd = models.CharField(db_column='Bank_AccNumPWD', max_length=6, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    bank_acctype = models.CharField(db_column='Bank_AccType', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    identitynumber = models.CharField(db_column='IdentityNumber', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    accountname = models.CharField(db_column='AccountName', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    bankid = models.CharField(db_column='BankID', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    fastid = models.CharField(db_column='FastID', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    fastpwd = models.CharField(db_column='FastPWD', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    useperiod = models.IntegerField(db_column='UsePeriod')  # Field name made lowercase.
    memo = models.CharField(max_length=200, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    crt_dt = models.DateTimeField(db_column='Crt_Dt', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_BankAccForm'


class TblBanks(models.Model):
    code = models.CharField(db_column='CODE', max_length=2, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    name = models.CharField(db_column='NAME', max_length=40, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    remark = models.CharField(db_column='REMARK', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_Banks'


class TblBizcode(models.Model):
    attribute_year = models.IntegerField(db_column='Attribute_Year')  # Field name made lowercase.
    std_incm_rt_dd = models.CharField(db_column='Std_Incm_Rt_Dd', max_length=6, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    busnsect_nm = models.CharField(db_column='Busnsect_Nm', max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    middle_nm = models.CharField(db_column='Middle_Nm', max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    detail_nm = models.CharField(db_column='Detail_Nm', max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    full_detail_nm = models.CharField(db_column='Full_Detail_Nm', max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_BizCode'


class TblDtsCode(models.Model):
    seq_no = models.AutoField(db_column='Seq_No', primary_key=True)  # Field name made lowercase.
    admin_id = models.CharField(db_column='Admin_ID', max_length=12, db_collation='Korean_Wansung_CS_AS')  # Field name made lowercase.
    t_name = models.CharField(db_column='T_Name', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    p_code1 = models.CharField(db_column='P_Code1', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    p_code2 = models.CharField(db_column='P_Code2', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    p_code3 = models.CharField(db_column='P_Code3', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    reg_date = models.DateTimeField(db_column='Reg_Date')  # Field name made lowercase.
    rt_yn = models.CharField(db_column='Rt_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    view_yn = models.CharField(db_column='View_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_Dts_Code'


class TblDtsCodeSip(models.Model):
    amt_ty = models.CharField(db_column='AMT_TY', primary_key=True, max_length=3, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tbl_name = models.CharField(db_column='Tbl_Name', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    eng_name = models.CharField(db_column='Eng_Name', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    kor_name = models.CharField(db_column='Kor_Name', max_length=80, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    etc = models.CharField(db_column='ETC', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    reg_date = models.CharField(db_column='Reg_Date', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    reg_id = models.CharField(db_column='Reg_ID', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_Dts_Code_SIP'


class TblEmploydetail(models.Model):
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    work_yy = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS')
    empjumin = models.CharField(db_column='empJumin', max_length=14, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    empsalary = models.DecimalField(db_column='empSalary', max_digits=18, decimal_places=0)  # Field name made lowercase.
    empincentive = models.DecimalField(db_column='empIncentive', max_digits=18, decimal_places=0)  # Field name made lowercase.
    empgranted = models.DecimalField(db_column='empGranted', max_digits=18, decimal_places=0)  # Field name made lowercase.
    empcontribution = models.DecimalField(db_column='empContribution', max_digits=18, decimal_places=0)  # Field name made lowercase.
    empcareer = models.CharField(db_column='empCareer', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    empdurunury = models.CharField(db_column='empDurunury', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    empcontract = models.CharField(db_column='empContract', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_EmployDetail'


class TblEmploytotsalary(models.Model):
    seq_no = models.CharField(db_column='Seq_no', primary_key=True, max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    work_yy = models.CharField(db_column='Work_yy', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    empnum = models.CharField(db_column='EmpNum', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    empname = models.CharField(db_column='EmpName', max_length=30, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    empjumin = models.CharField(db_column='EmpJumin', max_length=14, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    emptot = models.DecimalField(db_column='EmpTot', max_digits=13, decimal_places=0)  # Field name made lowercase.
    empjan = models.DecimalField(db_column='EmpJan', max_digits=13, decimal_places=0)  # Field name made lowercase.
    empfeb = models.DecimalField(db_column='EmpFeb', max_digits=13, decimal_places=0)  # Field name made lowercase.
    empmar = models.DecimalField(db_column='EmpMar', max_digits=13, decimal_places=0)  # Field name made lowercase.
    empapr = models.DecimalField(db_column='EmpApr', max_digits=13, decimal_places=0)  # Field name made lowercase.
    empmay = models.DecimalField(db_column='EmpMay', max_digits=13, decimal_places=0)  # Field name made lowercase.
    empjun = models.DecimalField(db_column='EmpJun', max_digits=13, decimal_places=0)  # Field name made lowercase.
    empjul = models.DecimalField(db_column='EmpJul', max_digits=13, decimal_places=0)  # Field name made lowercase.
    empaug = models.DecimalField(db_column='EmpAug', max_digits=13, decimal_places=0)  # Field name made lowercase.
    empsep = models.DecimalField(db_column='EmpSep', max_digits=13, decimal_places=0)  # Field name made lowercase.
    empoct = models.DecimalField(db_column='EmpOct', max_digits=13, decimal_places=0)  # Field name made lowercase.
    empnov = models.DecimalField(db_column='EmpNov', max_digits=13, decimal_places=0)  # Field name made lowercase.
    empdec = models.DecimalField(db_column='EmpDec', max_digits=13, decimal_places=0)  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_EmployTotSalary'
        unique_together = (('seq_no', 'work_yy', 'empnum'),)





class TblHealthInsu(models.Model):
    seq_no = models.AutoField(db_column='Seq_No', primary_key=True)  # Field name made lowercase.
    cate = models.CharField(db_column='Cate', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    flag = models.CharField(db_column='Flag', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    std_num = models.FloatField(db_column='Std_Num')  # Field name made lowercase.
    point = models.FloatField(db_column='Point')  # Field name made lowercase.
    remk = models.CharField(db_column='Remk', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_Health_Insu'


class TblHometaxCashsales(models.Model):
    tran_yy = models.CharField(db_column='Tran_YY', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    tran_dt = models.CharField(db_column='Tran_Dt', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    stnd_gb = models.CharField(db_column='Stnd_GB', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    stnd_sdt = models.CharField(db_column='Stnd_SDt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    stnd_edt = models.CharField(db_column='Stnd_EDt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    seq_no = models.CharField(db_column='Seq_No', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    biz_name = models.CharField(max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    cshpttrstypenm = models.CharField(db_column='cshptTrsTypeNm', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    splcft = models.DecimalField(db_column='splCft', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    vatxamt = models.DecimalField(db_column='vaTxamt', max_digits=11, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    tip = models.DecimalField(max_digits=11, decimal_places=0, blank=True, null=True)
    totatrsamt = models.DecimalField(db_column='totaTrsAmt', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    aprvno = models.CharField(db_column='aprvNo', max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    trsclnm = models.CharField(db_column='trsClNm', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    trsclcd = models.CharField(db_column='trsClCd', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    pblclcd = models.CharField(db_column='pblClCd', max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    spstcnfrpartno = models.CharField(db_column='spstCnfrPartNo', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    rcprtxprnm = models.CharField(db_column='rcprTxprNm', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    spstcnfrclnm = models.CharField(db_column='spstCnfrClNm', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    cshptusgclnm = models.CharField(db_column='cshptUsgClNm', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crt_dt = models.DateTimeField(db_column='Crt_Dt', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_HomeTax_CashSales'


class TblHometaxSalecard(models.Model):
    tran_yy = models.CharField(db_column='Tran_YY', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    seq_no = models.CharField(db_column='Seq_No', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    salegubun = models.CharField(db_column='SaleGubun', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    stnd_gb = models.CharField(db_column='Stnd_GB', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_mm = models.CharField(db_column='Tran_MM', max_length=6, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    mm_scnt = models.DecimalField(db_column='MM_Scnt', max_digits=9, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    tot_stlamt = models.DecimalField(db_column='Tot_StlAmt', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    etc_stlamt = models.DecimalField(db_column='Etc_StlAmt', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    purceucardamt = models.DecimalField(db_column='PurcEuCardAmt', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    tipamt = models.DecimalField(db_column='TipAmt', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    crt_dt = models.DateTimeField(db_column='Crt_Dt', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_HomeTax_SaleCard'


class TblHometaxScrap(models.Model):
    tran_yy = models.CharField(db_column='Tran_YY', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    tran_dt = models.CharField(db_column='Tran_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    tran_chkseq = models.CharField(db_column='Tran_chkseq', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    stnd_gb = models.CharField(db_column='Stnd_GB', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    stnd_sdt = models.CharField(db_column='Stnd_SDt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    stnd_edt = models.CharField(db_column='Stnd_EDt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    hometaxid = models.CharField(db_column='HomeTaxId', max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    hometaxpw = models.CharField(db_column='HomeTaxPW', max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    biz_no = models.CharField(db_column='Biz_No', max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    seq_no = models.CharField(db_column='Seq_No', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    rowseq = models.IntegerField(db_column='RowSeq', blank=True, null=True)  # Field name made lowercase.
    biz_name = models.CharField(max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    biz_card_ty = models.CharField(db_column='Biz_Card_TY', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    aprvdt = models.CharField(db_column='AprvDt', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crcmclnm = models.CharField(db_column='CrcmClNm', max_length=60, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    busncrdcardnoenccntn = models.CharField(db_column='busnCrdCardNoEncCntn', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    mrnttxprdscmnoenccntn = models.CharField(db_column='mrntTxprDscmNoEncCntn', max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    mrnttxprnm = models.CharField(db_column='mrntTxprNm', max_length=200, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    splcft = models.DecimalField(db_column='splCft', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    vatxamt = models.DecimalField(db_column='vaTxamt', max_digits=11, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    tip = models.DecimalField(max_digits=11, decimal_places=0, blank=True, null=True)
    totatrsamt = models.DecimalField(db_column='totaTrsAmt', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    bmanclnm = models.CharField(db_column='bmanClNm', max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    ddcynnm = models.CharField(db_column='ddcYnNm', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    vatddcclnm = models.CharField(db_column='vatDdcClNm', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    vatchkty = models.CharField(db_column='VatChkTY', max_length=2, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    file_ddctgb = models.CharField(db_column='File_DdctGB', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='Acnt_Cd', max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    acnt_nm = models.CharField(db_column='Acnt_Nm', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    gerenel_ty = models.CharField(db_column='Gerenel_Ty', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crt_dt = models.DateTimeField(db_column='Crt_Dt', blank=True, null=True)  # Field name made lowercase.
    db_ins_yn = models.CharField(db_column='Db_Ins_YN', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    db_ins_dt = models.DateTimeField(db_column='Db_Ins_Dt', blank=True, null=True)  # Field name made lowercase.
    file_mk_yn = models.CharField(db_column='File_MK_YN', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    file_mk_dt = models.DateTimeField(db_column='File_MK_Dt', blank=True, null=True)  # Field name made lowercase.
    wk_gb = models.CharField(db_column='WK_GB', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    lawrsn = models.CharField(db_column='lawRsn', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_HomeTax_Scrap'


class TblHometaxScrapHy(models.Model):
    tran_yy = models.CharField(db_column='Tran_YY', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    tran_dt = models.CharField(db_column='Tran_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    tran_chkseq = models.CharField(db_column='Tran_chkseq', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    stnd_gb = models.CharField(db_column='Stnd_GB', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    stnd_sdt = models.CharField(db_column='Stnd_SDt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    stnd_edt = models.CharField(db_column='Stnd_EDt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    hometaxid = models.CharField(db_column='HomeTaxId', max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    hometaxpw = models.CharField(db_column='HomeTaxPW', max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    biz_no = models.CharField(db_column='Biz_No', max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    seq_no = models.CharField(db_column='Seq_No', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    rowseq = models.IntegerField(db_column='RowSeq', blank=True, null=True)  # Field name made lowercase.
    biz_name = models.CharField(max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    biz_card_ty = models.CharField(db_column='Biz_Card_TY', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    aprvdt = models.CharField(db_column='AprvDt', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crcmclnm = models.CharField(db_column='CrcmClNm', max_length=60, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    busncrdcardnoenccntn = models.CharField(db_column='busnCrdCardNoEncCntn', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    mrnttxprdscmnoenccntn = models.CharField(db_column='mrntTxprDscmNoEncCntn', max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    mrnttxprnm = models.CharField(db_column='mrntTxprNm', max_length=60, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    splcft = models.DecimalField(db_column='splCft', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    vatxamt = models.DecimalField(db_column='vaTxamt', max_digits=11, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    tip = models.DecimalField(max_digits=11, decimal_places=0, blank=True, null=True)
    totatrsamt = models.DecimalField(db_column='totaTrsAmt', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    bmanclnm = models.CharField(db_column='bmanClNm', max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    ddcynnm = models.CharField(db_column='ddcYnNm', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    vatddcclnm = models.CharField(db_column='vatDdcClNm', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    vatchkty = models.CharField(db_column='VatChkTY', max_length=2, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    file_ddctgb = models.CharField(db_column='File_DdctGB', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='Acnt_Cd', max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    acnt_nm = models.CharField(db_column='Acnt_Nm', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    gerenel_ty = models.CharField(db_column='Gerenel_Ty', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crt_dt = models.DateTimeField(db_column='Crt_Dt', blank=True, null=True)  # Field name made lowercase.
    db_ins_yn = models.CharField(db_column='Db_Ins_YN', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    db_ins_dt = models.DateTimeField(db_column='Db_Ins_Dt', blank=True, null=True)  # Field name made lowercase.
    file_mk_yn = models.CharField(db_column='File_MK_YN', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    file_mk_dt = models.DateTimeField(db_column='File_MK_Dt', blank=True, null=True)  # Field name made lowercase.
    wk_gb = models.CharField(db_column='WK_GB', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_HomeTax_Scrap_HY'


class TblMail(models.Model):
    seq_no = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS')
    admin_name = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    biz_manager = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    biz_name = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    mail_subject = models.CharField(max_length=500, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    mail_content = models.TextField(db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    mail_to = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    mail_from = models.CharField(max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    mail_cc = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    mail_date = models.DateTimeField(blank=True, null=True)
    file_cnt = models.CharField(max_length=2, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    file_path = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    file_name = models.TextField(db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    mail_class = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Tbl_Mail'


class TblMinWages(models.Model):
    yy = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    min_wages = models.IntegerField(db_column='Min_Wages', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_Min_Wages'


class TblOfstKakaoSms(models.Model):
    seq_user = models.CharField(db_column='Seq_User', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    biz_name = models.CharField(db_column='Biz_Name', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    user_hpno = models.CharField(db_column='User_Hpno', max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    contents = models.TextField(db_column='Contents', db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase. This field type is a guess.
    btn_link = models.CharField(db_column='Btn_Link', max_length=200, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    kakao_tempcode = models.CharField(db_column='Kakao_tempCode', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    send_result = models.CharField(db_column='Send_Result', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    flag_dt = models.CharField(db_column='flag_Dt', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    send_dt = models.CharField(db_column='Send_Dt', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_OFST_KAKAO_SMS'


class TblRate(models.Model):
    seq_no = models.AutoField(db_column='Seq_No', primary_key=True)  # Field name made lowercase.
    rate_code = models.CharField(db_column='Rate_Code', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    rate_yup = models.CharField(db_column='Rate_Yup', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    rate_jong = models.CharField(db_column='Rate_Jong', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    rate_comment = models.CharField(db_column='Rate_Comment', max_length=2000, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    rate_simple = models.FloatField(db_column='Rate_Simple', blank=True, null=True)  # Field name made lowercase.
    rate_simple_add = models.FloatField(db_column='Rate_Simple_Add', blank=True, null=True)  # Field name made lowercase.
    rate_basic = models.FloatField(db_column='Rate_Basic', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_Rate'
        unique_together = (('seq_no', 'rate_code'),)


class TblSms(models.Model):
    seq_no = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS')
    sms_class = models.CharField(max_length=50, db_collation='Korean_Wansung_CI_AS')
    sms_send_dt = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS')
    sms_send_result = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS')
    sms_contents = models.TextField(db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # This field type is a guess.
    sms_tel_no = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS')

    class Meta:
        managed = False
        db_table = 'Tbl_SMS'


class TblSingogb(models.Model):
    yy = models.CharField(db_column='YY', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    gb_code = models.CharField(db_column='GB_Code', max_length=2, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    gb_sbookamt = models.DecimalField(db_column='Gb_SBookAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    gb_sestamt = models.DecimalField(db_column='Gb_SEstAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    gb_upcode = models.CharField(db_column='Gb_UpCode', max_length=200, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_SingoGB'


class TblStckhlisttrn(models.Model):
    seq_no = models.CharField(db_column='Seq_no', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    stckh_nm = models.CharField(db_column='StckH_Nm', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    stckh_num = models.CharField(db_column='StckH_Num', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_seqno = models.IntegerField(db_column='Tran_Seqno')  # Field name made lowercase.
    tran_dt = models.CharField(db_column='Tran_Dt', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    stckh_trangb = models.CharField(db_column='StckH_TranGB', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    stckh_ty = models.CharField(db_column='StckH_TY', max_length=2, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    stckh_trnsnm = models.CharField(db_column='StckH_TrnsNm', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    stckh_fequitynum = models.FloatField(db_column='StckH_FEquityNum')  # Field name made lowercase.
    stckh_fequityfp = models.FloatField(db_column='StckH_FEquityFP')  # Field name made lowercase.
    stckh_fequitygp = models.FloatField(db_column='StckH_FEquityGP')  # Field name made lowercase.
    stckh_regdt = models.CharField(db_column='StckH_RegDt', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_StckHListTrn'


class TblStckholderlist(models.Model):
    seq_no = models.CharField(db_column='Seq_no', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    stckh_num = models.CharField(db_column='StckH_Num', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    stckh_nm = models.CharField(db_column='StckH_Nm', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    stckh_jumin = models.CharField(db_column='StckH_Jumin', max_length=15, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    stckh_gb = models.CharField(db_column='StckH_GB', max_length=15, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    stckh_rs = models.CharField(db_column='StckH_RS', max_length=2, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    stckh_zipcode = models.CharField(db_column='StckH_ZipCode', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    stckh_addr1 = models.CharField(db_column='StckH_Addr1', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    stckh_addr2 = models.CharField(db_column='StckH_Addr2', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    stckh_equitydt = models.CharField(db_column='StckH_EquityDt', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    stckh_equitynum = models.FloatField(db_column='StckH_EquityNum')  # Field name made lowercase.
    stckh_equityfp = models.FloatField(db_column='StckH_EquityFP')  # Field name made lowercase.
    stckh_equitygp = models.FloatField(db_column='StckH_EquityGP')  # Field name made lowercase.
    stckh_fequitydt = models.CharField(db_column='StckH_FEquityDt', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    stckh_fequitynum = models.FloatField(db_column='StckH_FEquityNum')  # Field name made lowercase.
    stckh_fequityfp = models.FloatField(db_column='StckH_FEquityFP')  # Field name made lowercase.
    stckh_fequitygp = models.FloatField(db_column='StckH_FEquityGP')  # Field name made lowercase.
    stckh_regdt = models.CharField(db_column='StckH_RegDt', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_StckHolderList'


class TblTaxation(models.Model):
    taxation_code = models.CharField(db_column='Taxation_Code', max_length=3, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    area_code = models.CharField(db_column='Area_Code', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    taxation_name = models.CharField(db_column='Taxation_Name', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    taxation_acc = models.CharField(db_column='Taxation_Acc', max_length=6, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_Taxation'


class TblWorkcondition(models.Model):
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    empnum = models.CharField(db_column='empNum', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    regdt = models.CharField(db_column='RegDt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    mon = models.CharField(db_column='Mon', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    mon_stime = models.DecimalField(db_column='Mon_Stime', max_digits=4, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    mon_eime = models.DecimalField(db_column='Mon_Eime', max_digits=4, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    tue = models.CharField(db_column='Tue', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    tue_stime = models.DecimalField(db_column='Tue_Stime', max_digits=4, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    tue_eime = models.DecimalField(db_column='Tue_Eime', max_digits=4, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    wed = models.CharField(db_column='Wed', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    wed_stime = models.DecimalField(db_column='Wed_Stime', max_digits=4, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    wed_eime = models.DecimalField(db_column='Wed_Eime', max_digits=4, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    thu = models.CharField(db_column='Thu', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    thu_stime = models.DecimalField(db_column='Thu_Stime', max_digits=4, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    thu_eime = models.DecimalField(db_column='Thu_Eime', max_digits=4, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    fri = models.CharField(db_column='Fri', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    fri_stime = models.DecimalField(db_column='Fri_Stime', max_digits=4, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    fri_eime = models.DecimalField(db_column='Fri_Eime', max_digits=4, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    sat = models.CharField(db_column='Sat', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    sat_stime = models.DecimalField(db_column='Sat_Stime', max_digits=4, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    sat_eime = models.DecimalField(db_column='Sat_Eime', max_digits=4, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    sun = models.CharField(db_column='Sun', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    sun_stime = models.DecimalField(db_column='Sun_Stime', max_digits=4, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    sun_eime = models.DecimalField(db_column='Sun_Eime', max_digits=4, decimal_places=2, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_WorkCondition'


class TblWorkstate(models.Model):
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    empnum = models.CharField(db_column='empNum', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    workyy = models.CharField(db_column='WorkYY', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    workmm = models.CharField(db_column='WorkMM', max_length=2, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    workgb = models.CharField(db_column='WorkGB', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d1 = models.CharField(db_column='D1', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d2 = models.CharField(db_column='D2', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d3 = models.CharField(db_column='D3', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d4 = models.CharField(db_column='D4', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d5 = models.CharField(db_column='D5', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d6 = models.CharField(db_column='D6', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d7 = models.CharField(db_column='D7', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d8 = models.CharField(db_column='D8', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d9 = models.CharField(db_column='D9', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d10 = models.CharField(db_column='D10', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d11 = models.CharField(db_column='D11', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d12 = models.CharField(db_column='D12', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d13 = models.CharField(db_column='D13', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d14 = models.CharField(db_column='D14', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d15 = models.CharField(db_column='D15', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d16 = models.CharField(db_column='D16', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d17 = models.CharField(db_column='D17', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d18 = models.CharField(db_column='D18', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d19 = models.CharField(db_column='D19', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d20 = models.CharField(db_column='D20', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d21 = models.CharField(db_column='D21', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d22 = models.CharField(db_column='D22', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d23 = models.CharField(db_column='D23', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d24 = models.CharField(db_column='D24', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d25 = models.CharField(db_column='D25', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d26 = models.CharField(db_column='D26', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d27 = models.CharField(db_column='D27', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d28 = models.CharField(db_column='D28', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d29 = models.CharField(db_column='D29', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d30 = models.CharField(db_column='D30', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    d31 = models.CharField(db_column='D31', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    regdt = models.CharField(db_column='RegDT', max_length=12, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Tbl_WorkState'


class TempSbookComp(models.Model):
    tran_dt = models.CharField(db_column='Tran_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_no = models.CharField(db_column='IBO_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    slip_no = models.CharField(db_column='Slip_No', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    t_name = models.CharField(db_column='T_Name', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Temp_Sbook_Comp'


class Temp(models.Model):
    old_acnt_nm = models.CharField(db_column='Old_acnt_nm', max_length=60, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    acnt_cd = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    acnt_nm = models.CharField(max_length=60, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Temp_계정과목연결'


class TraderComp(models.Model):
    trader_seq = models.AutoField(db_column='Trader_Seq', primary_key=True)  # Field name made lowercase.
    ibo_no = models.CharField(db_column='Ibo_No', max_length=23, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    trader_id = models.CharField(db_column='Trader_Id', max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    trader_nm = models.CharField(db_column='Trader_Nm', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    trader_rep = models.CharField(db_column='Trader_Rep', max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    trader_jumin = models.CharField(db_column='Trader_Jumin', max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    trader_email = models.CharField(db_column='Trader_Email', max_length=60, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    trader_tel = models.CharField(db_column='Trader_Tel', max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    trader_fax = models.CharField(db_column='Trader_Fax', max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    trader_offaddr = models.CharField(db_column='Trader_OffAddr', max_length=200, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    trader_offzip = models.CharField(db_column='Trader_OffZip', max_length=6, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    trader_uptae = models.CharField(db_column='Trader_UpTae', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    trader_jmok = models.CharField(db_column='Trader_Jmok', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    trader_cate = models.CharField(db_column='Trader_Cate', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    up_dt = models.DateTimeField(db_column='Up_Dt', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Trader_Comp'


class VatBill(models.Model):
    seq_no = models.AutoField(db_column='Seq_No', primary_key=True)  # Field name made lowercase.
    ibo_no = models.CharField(db_column='Ibo_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_cate = models.CharField(db_column='Biz_Cate', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    bill_code = models.CharField(db_column='Bill_Code', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    bill_date = models.CharField(db_column='Bill_Date', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    bill_flag = models.CharField(db_column='Bill_Flag', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    bill_num = models.IntegerField(db_column='Bill_Num')  # Field name made lowercase.
    card_no = models.CharField(db_column='Card_No', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_name = models.CharField(db_column='Biz_Name', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_flag = models.CharField(db_column='Biz_Flag', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_no = models.CharField(db_column='Biz_No', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    supply_amt = models.DecimalField(db_column='Supply_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    tax_amt = models.DecimalField(db_column='Tax_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    tax_flag = models.CharField(db_column='Tax_Flag', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    p_flag = models.CharField(db_column='P_Flag', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    reg_date = models.CharField(db_column='Reg_Date', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    up_date = models.CharField(db_column='Up_Date', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    vat_flag = models.CharField(db_column='Vat_Flag', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Vat_Bill'


class VatBillCode(models.Model):
    seq_no = models.AutoField(db_column='Seq_No', primary_key=True)  # Field name made lowercase.
    biz_cate = models.CharField(db_column='Biz_Cate', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    bill_code = models.CharField(db_column='Bill_Code', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    code_name = models.CharField(db_column='Code_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    basic_yn = models.CharField(db_column='Basic_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    reduce_yn = models.CharField(db_column='Reduce_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    del_yn = models.CharField(db_column='Del_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Vat_Bill_Code'


class VatBillEnd(models.Model):
    seq_no = models.IntegerField(db_column='Seq_No')  # Field name made lowercase.
    ibo_no = models.CharField(db_column='Ibo_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_cate = models.CharField(db_column='Biz_Cate', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    bill_code = models.CharField(db_column='Bill_Code', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    bill_date = models.CharField(db_column='Bill_Date', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    bill_flag = models.CharField(db_column='Bill_Flag', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    bill_num = models.IntegerField(db_column='Bill_Num')  # Field name made lowercase.
    card_no = models.CharField(db_column='Card_No', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_name = models.CharField(db_column='Biz_Name', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_flag = models.CharField(db_column='Biz_Flag', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_no = models.CharField(db_column='Biz_No', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    supply_amt = models.DecimalField(db_column='Supply_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    tax_amt = models.DecimalField(db_column='Tax_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    tax_flag = models.CharField(db_column='Tax_Flag', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    p_flag = models.CharField(db_column='P_Flag', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    reg_date = models.CharField(db_column='Reg_Date', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    up_date = models.CharField(db_column='Up_Date', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    vat_flag = models.CharField(db_column='Vat_Flag', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Vat_Bill_End'


class VatReport(models.Model):
    seq_no = models.AutoField(db_column='Seq_No', primary_key=True)  # Field name made lowercase.
    ibo_no = models.CharField(db_column='Ibo_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_type = models.CharField(db_column='Ibo_Type', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_type = models.IntegerField(db_column='Biz_Type')  # Field name made lowercase.
    name = models.CharField(db_column='Name', max_length=30, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    email = models.CharField(db_column='Email', max_length=60, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    zipcode = models.CharField(db_column='Zipcode', max_length=7, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    addr1 = models.CharField(db_column='Addr1', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    addr2 = models.CharField(db_column='Addr2', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    tel_no = models.CharField(db_column='Tel_No', max_length=14, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    hp_no = models.CharField(db_column='Hp_No', max_length=14, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_no = models.CharField(db_column='Biz_No', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_name = models.CharField(db_column='Biz_Name', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ceo_name = models.CharField(db_column='Ceo_Name', max_length=30, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_zipcode = models.CharField(db_column='Biz_Zipcode', max_length=7, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_addr1 = models.CharField(db_column='Biz_Addr1', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_addr2 = models.CharField(db_column='Biz_Addr2', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_tel = models.CharField(db_column='Biz_Tel', max_length=14, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_taxation = models.CharField(db_column='Biz_Taxation', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_taxoffice_code = models.CharField(db_column='Biz_TaxOffice_Code', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_taxbank_acc = models.CharField(db_column='Biz_TaxBank_Acc', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_start_day = models.CharField(db_column='Biz_Start_Day', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_end_day = models.CharField(db_column='Biz_End_Day', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_end_reason = models.CharField(db_column='Biz_End_Reason', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ret_bank_code = models.CharField(db_column='Ret_Bank_Code', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ret_bank_name = models.CharField(db_column='Ret_Bank_Name', max_length=30, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ret_account = models.CharField(db_column='Ret_Account', max_length=30, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    pre_return_amt = models.DecimalField(db_column='Pre_Return_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    pre_notice_amt = models.DecimalField(db_column='Pre_Notice_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    reduce_tax45 = models.DecimalField(db_column='Reduce_Tax45', max_digits=13, decimal_places=0)  # Field name made lowercase.
    reduce_tax12 = models.DecimalField(db_column='Reduce_Tax12', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    singo_flag = models.CharField(db_column='Singo_Flag', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    singo_no = models.CharField(db_column='Singo_No', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    et_clm_yn = models.CharField(db_column='Et_Clm_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    sale_ta = models.DecimalField(db_column='Sale_TA', max_digits=13, decimal_places=0)  # Field name made lowercase.
    buy_ta = models.DecimalField(db_column='Buy_TA', max_digits=13, decimal_places=0)  # Field name made lowercase.
    reduce_ta = models.DecimalField(db_column='Reduce_TA', max_digits=13, decimal_places=0)  # Field name made lowercase.
    reg_date = models.DateTimeField(db_column='Reg_Date')  # Field name made lowercase.
    up_date = models.DateTimeField(db_column='Up_Date', blank=True, null=True)  # Field name made lowercase.
    vat_flag = models.CharField(db_column='Vat_Flag', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Vat_Report'


class VatReportEnd(models.Model):
    seq_no = models.IntegerField(db_column='Seq_No')  # Field name made lowercase.
    ibo_no = models.CharField(db_column='Ibo_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_type = models.CharField(db_column='Ibo_Type', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_type = models.IntegerField(db_column='Biz_Type')  # Field name made lowercase.
    name = models.CharField(db_column='Name', max_length=30, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    email = models.CharField(db_column='Email', max_length=60, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    zipcode = models.CharField(db_column='Zipcode', max_length=7, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    addr1 = models.CharField(db_column='Addr1', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    addr2 = models.CharField(db_column='Addr2', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    tel_no = models.CharField(db_column='Tel_No', max_length=14, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    hp_no = models.CharField(db_column='Hp_No', max_length=14, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_no = models.CharField(db_column='Biz_No', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_name = models.CharField(db_column='Biz_Name', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ceo_name = models.CharField(db_column='Ceo_Name', max_length=30, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_zipcode = models.CharField(db_column='Biz_Zipcode', max_length=7, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_addr1 = models.CharField(db_column='Biz_Addr1', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_addr2 = models.CharField(db_column='Biz_Addr2', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_tel = models.CharField(db_column='Biz_Tel', max_length=14, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_taxation = models.CharField(db_column='Biz_Taxation', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_taxoffice_code = models.CharField(db_column='Biz_TaxOffice_Code', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_taxbank_acc = models.CharField(db_column='Biz_TaxBank_Acc', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_start_day = models.CharField(db_column='Biz_Start_Day', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_end_day = models.CharField(db_column='Biz_End_Day', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    biz_end_reason = models.CharField(db_column='Biz_End_Reason', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ret_bank_code = models.CharField(db_column='Ret_Bank_Code', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ret_bank_name = models.CharField(db_column='Ret_Bank_Name', max_length=30, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ret_account = models.CharField(db_column='Ret_Account', max_length=30, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    pre_return_amt = models.DecimalField(db_column='Pre_Return_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    pre_notice_amt = models.DecimalField(db_column='Pre_Notice_Amt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    reduce_tax45 = models.DecimalField(db_column='Reduce_Tax45', max_digits=13, decimal_places=0)  # Field name made lowercase.
    reduce_tax12 = models.DecimalField(db_column='Reduce_Tax12', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    singo_flag = models.CharField(db_column='Singo_Flag', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    singo_no = models.CharField(db_column='Singo_No', max_length=50, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    et_clm_yn = models.CharField(db_column='Et_Clm_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    sale_ta = models.DecimalField(db_column='Sale_TA', max_digits=13, decimal_places=0)  # Field name made lowercase.
    buy_ta = models.DecimalField(db_column='Buy_TA', max_digits=13, decimal_places=0)  # Field name made lowercase.
    reduce_ta = models.DecimalField(db_column='Reduce_TA', max_digits=13, decimal_places=0)  # Field name made lowercase.
    reg_date = models.DateTimeField(db_column='Reg_Date')  # Field name made lowercase.
    up_date = models.DateTimeField(db_column='Up_Date', blank=True, null=True)  # Field name made lowercase.
    vat_flag = models.CharField(db_column='Vat_Flag', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Vat_Report_End'


class VatStep(models.Model):
    seq_no = models.AutoField(db_column='Seq_No', primary_key=True)  # Field name made lowercase.
    ibo_no = models.CharField(db_column='Ibo_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    vat_step = models.IntegerField(db_column='Vat_Step')  # Field name made lowercase.
    reg_date = models.DateTimeField(db_column='Reg_Date')  # Field name made lowercase.
    up_date = models.DateTimeField(db_column='Up_Date', blank=True, null=True)  # Field name made lowercase.
    vat_flag = models.CharField(db_column='Vat_Flag', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Vat_Step'


class Workgong(models.Model):
    yy = models.CharField(db_column='YY', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ddct_samt = models.DecimalField(db_column='Ddct_Samt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    ddct_eamt = models.DecimalField(db_column='Ddct_Eamt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    ddct_gongamt = models.DecimalField(db_column='Ddct_GongAmt', max_digits=13, decimal_places=0)  # Field name made lowercase.
    ddct_gongrate = models.CharField(db_column='Ddct_GongRate', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    mdfy_dt = models.CharField(db_column='Mdfy_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'WorkGong'


class Worktax(models.Model):
    yy = models.CharField(db_column='YY', primary_key=True, max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    taxat_stand_min = models.DecimalField(max_digits=13, decimal_places=0)
    taxat_stand_max = models.DecimalField(max_digits=13, decimal_places=0)
    taxrat = models.DecimalField(max_digits=5, decimal_places=2)
    prgrs_ddct_amt = models.DecimalField(max_digits=13, decimal_places=0)
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    mdfy_dt = models.CharField(db_column='Mdfy_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'WorkTax'
        unique_together = (('yy', 'taxat_stand_min', 'taxat_stand_max'),)







class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    object_repr = models.CharField(max_length=200, db_collation='Korean_Wansung_CI_AS')
    action_flag = models.SmallIntegerField()
    change_message = models.TextField(db_collation='Korean_Wansung_CI_AS')
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS')
    model = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS')

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS')
    name = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS')
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40, db_collation='Korean_Wansung_CI_AS')
    session_data = models.TextField(db_collation='Korean_Wansung_CI_AS')
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class DsMonth(models.Model):
    ds_month = models.CharField(max_length=2, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ds_month'


class DsSlipledgr33(models.Model):
    seq_no = models.CharField(db_column='Seq_No', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    work_yy = models.CharField(db_column='Work_YY', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='Acnt_cd', max_length=3, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_nm = models.CharField(db_column='Acnt_Nm', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_dt = models.CharField(db_column='Tran_Dt', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    remk = models.CharField(db_column='Remk', max_length=500, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_code = models.CharField(db_column='Trader_Code', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_name = models.CharField(db_column='Trader_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_bizno = models.CharField(db_column='Trader_Bizno', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    slip_no = models.CharField(db_column='Slip_No', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_stat = models.CharField(db_column='Tran_Stat', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crdr = models.CharField(db_column='CrDr', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tranamt_cr = models.DecimalField(db_column='TranAmt_Cr', max_digits=15, decimal_places=0)  # Field name made lowercase.
    tranamt_dr = models.DecimalField(db_column='TranAmt_Dr', max_digits=15, decimal_places=0)  # Field name made lowercase.
    employee_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    employee_name = models.CharField(db_column='employee_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    credit_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    credit_name = models.CharField(db_column='credit_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    place_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    place_name = models.CharField(db_column='place_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    project_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    project_name = models.CharField(db_column='project_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    cncl_dt = models.CharField(db_column='Cncl_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ds_slipledgr33'


class FinancialSpcacnt(models.Model):
    seq_no = models.CharField(db_column='Seq_No', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    financial_acntcd = models.CharField(db_column='Financial_AcntCd', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_acntnm = models.CharField(db_column='Financial_AcntNm', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_trnacntnm = models.CharField(db_column='Financial_TrnAcntNm', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    debt_cr_ty = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'financial_SpcAcnt'


class FinancialAcntnm3(models.Model):
    financial_gb = models.CharField(db_column='Financial_GB', max_length=7, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_acntty = models.CharField(db_column='Financial_AcntTy', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_acntnm = models.CharField(db_column='Financial_AcntNm', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_trnacntnm = models.CharField(db_column='Financial_TrnAcntNm', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_acntcd = models.CharField(db_column='Financial_AcntCd', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    debt_cr_ty = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    acnt_attrb = models.CharField(max_length=7, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    tot_attrb = models.CharField(max_length=7, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    adv_tot_ty = models.CharField(max_length=7, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    tot_acnt_cd = models.CharField(max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    prt_ord = models.IntegerField(db_column='Prt_Ord', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'financial_acntnm3'


class FinancialAcntnm5(models.Model):
    financial_gb = models.CharField(db_column='Financial_GB', max_length=7, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_acntty = models.CharField(db_column='Financial_AcntTy', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_acntnm = models.CharField(db_column='Financial_AcntNm', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_trnacntnm = models.CharField(db_column='Financial_TrnAcntNm', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_acntcd = models.CharField(db_column='Financial_AcntCd', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    debt_cr_ty = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    acnt_attrb = models.CharField(max_length=7, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    tot_attrb = models.CharField(max_length=7, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    adv_tot_ty = models.CharField(max_length=7, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    tot_acnt_cd = models.CharField(max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    prt_ord = models.IntegerField(db_column='Prt_Ord', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'financial_acntnm5'


class Haesole201912(models.Model):
    전표일자 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    전표번호 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    순번 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    계정 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    구분 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    계정명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    거래처 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    거래처명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    차변금액 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    대변금액 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    외화금액 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    적요 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    부서 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    부서명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    프로젝트 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    프로젝트명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    최종일자 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    관련업무발생구분 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'haesole201912'


class Haesolerookie2019(models.Model):
    전표일자 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    전표번호 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    순번 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    계정 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    구분 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    계정명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    거래처 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    거래처명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    차변금액 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    대변금액 = models.FloatField(blank=True, null=True)
    외화금액 = models.FloatField(blank=True, null=True)
    적요 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    부서 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    부서명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    프로젝트 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    프로젝트명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    최종일자 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    관련업무발생구분 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    f19 = models.CharField(db_column='F19', max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    f20 = models.CharField(db_column='F20', max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    f21 = models.CharField(db_column='F21', max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    f22 = models.CharField(db_column='F22', max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    f23 = models.CharField(db_column='F23', max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'haesoleRookie2019'


class Haesole202003(models.Model):
    전표일자 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    전표번호 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    순번 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    계정 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    구분 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    계정명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    거래처 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    거래처명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    차변금액 = models.FloatField(blank=True, null=True)
    대변금액 = models.FloatField(blank=True, null=True)
    외화금액 = models.FloatField(blank=True, null=True)
    적요 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    부서 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    부서명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    프로젝트 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    프로젝트명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    최종일자 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    관련업무발생구분 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'haesole_202003'


class Haesole20202(models.Model):
    전표일자 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    전표번호 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    순번 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    계정 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    구분 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    계정명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    거래처 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    거래처명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    차변금액 = models.FloatField(blank=True, null=True)
    대변금액 = models.FloatField(blank=True, null=True)
    외화금액 = models.FloatField(blank=True, null=True)
    적요 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    부서 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    부서명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    프로젝트 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    프로젝트명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    최종일자 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    관련업무발생구분 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'haesole_2020_2'


class HaesoleRookie(models.Model):
    전표일자 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    전표번호 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    순번 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    계정 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    구분 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    계정명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    거래처 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    거래처명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    차변금액 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    대변금액 = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    적요 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    부서 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    부서명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    프로젝트 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    프로젝트명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    최종일자 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    관련업무발생구분 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'haesole_Rookie'


class KakaoTemplatelist(models.Model):
    templatecode = models.CharField(db_column='templateCode', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    templatecontent = models.TextField(db_column='templateContent', db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    reg_date = models.CharField(max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'kakao_templateList'


class Lawregistration(models.Model):
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    execflag = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS')
    execnum = models.CharField(db_column='execNum', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    execname = models.CharField(db_column='execName', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    execjumin = models.CharField(db_column='execJumin', max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    regdate = models.CharField(db_column='regDate', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    extentdate = models.CharField(db_column='extentDate', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    firedate = models.CharField(db_column='fireDate', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    exechpno = models.CharField(db_column='execHpno', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    equitynum = models.FloatField(db_column='equityNum', blank=True, null=True)  # Field name made lowercase.
    equityfaceprice = models.FloatField(db_column='equityFacePrice', blank=True, null=True)  # Field name made lowercase.
    equitygainprice = models.FloatField(db_column='equityGainPrice', blank=True, null=True)  # Field name made lowercase.
    execzipcode = models.CharField(db_column='execZipcode', max_length=7, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    execaddr1 = models.CharField(db_column='execAddr1', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    execaddr2 = models.CharField(db_column='execAddr2', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    dk_fee = models.FloatField(db_column='DK_FEE', blank=True, null=True)  # Field name made lowercase.
    yn_fee = models.CharField(db_column='YN_FEE', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'lawRegistration'


class Newregistration(models.Model):
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    hometaxagreemanage = models.CharField(db_column='hometaxAgreeManage', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    hometaxidpwmanage = models.CharField(db_column='hometaxIDPWManage', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    hometaxbank = models.CharField(db_column='hometaxBank', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    hometaxcard = models.CharField(db_column='hometaxCard', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    intranetmanage = models.CharField(db_column='intranetManage', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    invoicemanage = models.CharField(db_column='invoiceManage', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    employmanage = models.CharField(db_column='employManage', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    taxschedulemanage = models.CharField(db_column='taxscheduleManage', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    taxassistmanage = models.CharField(db_column='taxassistManage', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    policymanage = models.CharField(db_column='policyManage', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    businessmanage = models.CharField(db_column='businessManage', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    insurancemanage = models.CharField(db_column='insuranceManage', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    etc1 = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    etc2 = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    etc3 = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    releaselisting = models.CharField(db_column='releaseListing', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'newRegistration'


class OfstSchedule(models.Model):
    seq_user = models.CharField(primary_key=True, max_length=5, db_collation='Korean_Wansung_CI_AS')
    choicha = models.CharField(max_length=2, db_collation='Korean_Wansung_CI_AS')
    pay_date = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    pay_kkka = models.DecimalField(db_column='pay_KKKA', max_digits=18, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    pay_vat = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    taxinvoice_yn = models.CharField(db_column='TaxInvoice_YN', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'ofst_schedule'
        unique_together = (('seq_user', 'choicha'),)


class ScrapCommon(models.Model):
    txt_keyword = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    ddct_yn = models.CharField(db_column='ddct_YN', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    ddct_acntcd = models.CharField(db_column='ddct_AcntCd', max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    lawrsn = models.CharField(db_column='lawRsn', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'scrap_common'


class ScrapCommonTmp(models.Model):
    mrnttxprnm = models.CharField(db_column='mrntTxprNm', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    ddct_yn = models.CharField(db_column='ddct_YN', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    ddct_acntcd = models.CharField(db_column='ddct_AcntCd', max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    lawrsn = models.CharField(db_column='lawRsn', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'scrap_common_tmp'


class ScrapEach(models.Model):
    seq_no = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    tot_ddct = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    tot_acntcd = models.CharField(db_column='tot_AcntCd', max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    car_ddct = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    car_class = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'scrap_each'


class SejinOrigin2017(models.Model):
    일자 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    번호 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    구분 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    계정과목 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    계정과목1 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    금액 = models.FloatField(blank=True, null=True)
    적요 = models.FloatField(blank=True, null=True)
    적요1 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    거래처명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    거래처명1 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    등록번호 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    대표자명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    자금 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    부서사원 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    부서사원1 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    현장명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    현장명1 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    프로젝트 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    프로젝트1 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    유형 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sejin_origin_2017'


class SejinOrigin2018(models.Model):
    일자 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    번호 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    구분 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    계정과목 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    계정과목1 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    금액 = models.FloatField(blank=True, null=True)
    적요 = models.FloatField(blank=True, null=True)
    적요1 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    거래처명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    거래처명1 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    등록번호 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    대표자명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    자금 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    부서사원 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    부서사원1 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    현장명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    현장명1 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    프로젝트 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    프로젝트1 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    유형 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sejin_origin_2018'


class Stone20202(models.Model):
    전표일자 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    전표번호 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    순번 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    계정 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    구분 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    계정명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    거래처 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    거래처명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    차변금액 = models.FloatField(blank=True, null=True)
    대변금액 = models.FloatField(blank=True, null=True)
    외화금액 = models.FloatField(blank=True, null=True)
    적요 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    부서 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    부서명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    프로젝트 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    프로젝트명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    최종일자 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    관련업무발생구분 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'stone_2020_2'


class TblDiscount(models.Model):
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    additiondc_yj = models.CharField(db_column='AdditionDC_YJ', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    additiondc_ddct = models.CharField(db_column='AdditionDC_Ddct', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    additiondc_stnd = models.CharField(db_column='AdditionDC_Stnd', max_length=2, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    additiondc_jbcnt = models.CharField(db_column='AdditionDC_JBCnt', max_length=2, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    saddition_rsn = models.CharField(db_column='Saddition_Rsn', max_length=200, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    saddition_amt = models.DecimalField(db_column='SAddition_Amt', max_digits=12, decimal_places=0)  # Field name made lowercase.
    oaddition_rsn = models.CharField(db_column='OAddition_Rsn', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    oaddition_amt = models.DecimalField(db_column='OAddition_Amt', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    faddition_rsn = models.CharField(db_column='FAddition_Rsn', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    faddition_amt = models.DecimalField(db_column='FAddition_amt', max_digits=12, decimal_places=0, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_Discount'

class TblFault(models.Model):
    admin_id = models.CharField(max_length=40)
    occurDate = models.DateField()
    biz_name = models.CharField(max_length=100, blank=True, null=True)
    faultAmt = models.IntegerField(default=0)
    reason = models.TextField(blank=True, null=True)
    AdaptOption = models.CharField(max_length=10, blank=True, null=True)
    id = models.AutoField(primary_key=True)
    class Meta:
        managed = False
        db_table = 'tbl_fault'
    def __str__(self):
        return f"{self.admin_id} - {self.occurDate}"


class TblEmploy(models.Model):
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    empnum = models.CharField(db_column='empNum', max_length=7, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    empjumin = models.CharField(db_column='empJumin', max_length=14, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    empname = models.CharField(db_column='empName', max_length=20, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    empbirth = models.CharField(db_column='empBirth', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    empregdate = models.CharField(db_column='empRegdate', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    empexitdate = models.CharField(db_column='empExitdate', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    empreject = models.CharField(db_column='empReject', max_length=30, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    emparmymm = models.CharField(db_column='empArmyMM', max_length=3, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    empdisable = models.CharField(db_column='empDisable', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    empbusoe = models.CharField(db_column='empBUSOE', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    emphpno = models.CharField(db_column='empHPNO', max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    empemail = models.CharField(db_column='empEMAIL', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    empsudang = models.DecimalField(db_column='empSUDANG', max_digits=12, decimal_places=0, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_Employ'


class TblEquityeval(models.Model):
    사업자번호 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    사업연도말 = models.CharField(max_length=6, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    법인등록번호 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    업태 = models.CharField(max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    종목 = models.CharField(max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    주업종코드 = models.CharField(max_length=6, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    사업연도 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    회사종류 = models.CharField(max_length=2, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    자산가액 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    자산가산1 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    자산가산2 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    자산가산3 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    자산차감1 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    자산차감2 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    부채가액 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    부채가산배당 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    부채가산퇴추 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    각사업연도소득 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    환급이자 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득가산배당 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득가산기부추인 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득공제벌금 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득공제공과금 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득공제업무무관 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득공제징수불 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득공제기부금 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득공제접대비 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득공제과다경비 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득공제지급이자 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득공제감비추인 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    법인세 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    농특세 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    지방세 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    익금유보 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    손금유보 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    결손금누계 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    최저한세적용대상 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    최저한세적용제외 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    수입금액 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    과세표준_법인세 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    과세표준_토지 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    과세표준_합계 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    산출세액_법인세 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    산출세액_토지 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    산출세액_합계 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    총부담세액_법인세 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    총부담세액_토지 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    총부담세액_합계 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    기납부세액_법인세 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    기납부세액_토지 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    기납부세액_합계 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    차감납부세액_법인세 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    차감납부세액_토지 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    차감납부세액_합계 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    분납세액 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    차감납부세액 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_EquityEval'


class TblEquityevalMid(models.Model):
    사업자번호 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    사업연도말 = models.CharField(max_length=6, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    법인등록번호 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    안내메일 = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    납부서메일 = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    주업종코드 = models.CharField(max_length=6, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    사업연도 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    중간예납신고방법 = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    자산가액 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    자산가산1 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    자산가산2 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    자산가산3 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    자산차감1 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    자산차감2 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    부채가액 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    부채가산배당 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    부채가산퇴추 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    각사업연도소득 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    환급이자 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득가산배당 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득가산기부추인 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득공제벌금 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득공제공과금 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득공제업무무관 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득공제징수불 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득공제기부금 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득공제접대비 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득공제과다경비 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득공제지급이자 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득공제감비추인 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    법인세 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    농특세 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    지방세 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    익금유보 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    손금유보 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    결손금누계 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    최저한세적용대상 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    최저한세적용제외 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    수입금액 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    과세표준_법인세 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    과세표준_토지 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    과세표준_합계 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    산출세액_법인세 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    산출세액_토지 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    산출세액_합계 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    총부담세액_법인세 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    총부담세액_토지 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    총부담세액_합계 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    기납부세액_법인세 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    기납부세액_토지 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    기납부세액_합계 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    차감납부세액_법인세 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    차감납부세액_토지 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    차감납부세액_합계 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    분납세액 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    차감납부세액 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_EquityEval_MID'


class TblPost(models.Model):
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    work_yy = models.CharField(db_column='work_YY', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    flag = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    post_yn = models.CharField(db_column='post_YN', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    post_date = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    post_way = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    post_bigo = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    post_printyn = models.CharField(db_column='post_printYN', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_Post'


class TblChenap(models.Model):
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    biz_name = models.CharField(max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    work_yy = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    work_mm = models.CharField(max_length=2, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    searchdate = models.CharField(db_column='searchDate', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    maildate = models.CharField(db_column='mailDate', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    taxmok = models.CharField(db_column='taxMok', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    taxamt = models.DecimalField(db_column='taxAmt', max_digits=18, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    taxnapbunum = models.CharField(db_column='taxNapbuNum', max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    taxoffice = models.CharField(db_column='taxOffice', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    taxduedate = models.CharField(db_column='taxDuedate', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_chenap'


class TblCorporate(models.Model):
    seq_no = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    work_yy = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    yn_1 = models.CharField(db_column='YN_1', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_2 = models.CharField(db_column='YN_2', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_3 = models.CharField(db_column='YN_3', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_4 = models.CharField(db_column='YN_4', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_5 = models.CharField(db_column='YN_5', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_6 = models.CharField(db_column='YN_6', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_7 = models.DecimalField(db_column='YN_7', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    yn_8 = models.CharField(db_column='YN_8', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_corporate'


class TblCorporate2(models.Model):
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    work_yy = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    yn_1 = models.DecimalField(db_column='YN_1', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    yn_2 = models.DecimalField(db_column='YN_2', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    yn_3 = models.DecimalField(db_column='YN_3', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    yn_4 = models.DecimalField(db_column='YN_4', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    yn_5 = models.DecimalField(db_column='YN_5', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    yn_6 = models.CharField(db_column='YN_6', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_7 = models.CharField(db_column='YN_7', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_8 = models.DecimalField(db_column='YN_8', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    yn_9 = models.CharField(db_column='YN_9', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_corporate2'


class TblEmpsalaryresult(models.Model):
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    empnum = models.CharField(db_column='empNum', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    empwc = models.CharField(db_column='empWC', max_length=14, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    work_yy = models.CharField(db_column='work_YY', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    work_mm = models.CharField(db_column='work_MM', max_length=2, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    salary_basic = models.CharField(db_column='salary_Basic', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    salary_extent = models.CharField(db_column='salary_Extent', max_length=200, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    salary_night = models.CharField(db_column='salary_Night', max_length=200, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    salary_bonus = models.TextField(db_column='salary_Bonus', db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_empSalaryResult'


class TblGoji(models.Model):
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    biz_name = models.CharField(max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    work_yy = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    work_mm = models.CharField(max_length=2, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    searchdate = models.CharField(db_column='searchDate', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    maildate = models.CharField(db_column='mailDate', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    taxmok = models.CharField(db_column='taxMok', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    taxamt = models.DecimalField(db_column='taxAmt', max_digits=18, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    taxnapbunum = models.CharField(db_column='taxNapbuNum', max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    taxoffice = models.CharField(db_column='taxOffice', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    taxduedate = models.CharField(db_column='taxDuedate', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_goji'


class TblIlyoung(models.Model):
    seq_no = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS')
    work_yy = models.CharField(db_column='work_YY', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    yn_1 = models.CharField(db_column='YN_1', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_2 = models.CharField(db_column='YN_2', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_3 = models.CharField(db_column='YN_3', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_4 = models.CharField(db_column='YN_4', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_5 = models.CharField(db_column='YN_5', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_6 = models.CharField(db_column='YN_6', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_7 = models.CharField(db_column='YN_7', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_8 = models.CharField(db_column='YN_8', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_9 = models.CharField(db_column='YN_9', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_10 = models.CharField(db_column='YN_10', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_11 = models.CharField(db_column='YN_11', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_12 = models.CharField(db_column='YN_12', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_13 = models.CharField(db_column='YN_13', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_ilyoung'


class TblIlyoung2(models.Model):
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    work_qt = models.CharField(db_column='work_QT', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_1 = models.CharField(db_column='YN_1', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_2 = models.CharField(db_column='YN_2', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_3 = models.CharField(db_column='YN_3', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_ilyoung2'


class TblIncome2(models.Model):
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    work_yy = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    yn_1 = models.FloatField(db_column='YN_1', blank=True, null=True)  # Field name made lowercase.
    yn_2 = models.FloatField(db_column='YN_2', blank=True, null=True)  # Field name made lowercase.
    yn_3 = models.FloatField(db_column='YN_3', blank=True, null=True)  # Field name made lowercase.
    yn_4 = models.FloatField(db_column='YN_4', blank=True, null=True)  # Field name made lowercase.
    yn_5 = models.FloatField(db_column='YN_5', blank=True, null=True)  # Field name made lowercase.
    yn_6 = models.CharField(db_column='YN_6', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_7 = models.CharField(db_column='YN_7', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_8 = models.FloatField(db_column='YN_8', blank=True, null=True)  # Field name made lowercase.
    yn_9 = models.CharField(db_column='YN_9', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_income2'


class TblKani(models.Model):
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    work_yy = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    work_banki = models.CharField(max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    txt_bigo = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_kani'


class TblMisu(models.Model):
    seq_no = models.CharField(max_length=6, db_collation='Korean_Wansung_CI_AS')
    work_yy = models.CharField(db_column='work_YY', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    title_tax = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    vat_kisu = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    isdaeson = models.CharField(db_column='isDaeson', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    occurdate = models.CharField(db_column='occurDate', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    txt_bigo = models.TextField(db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    misuamt = models.DecimalField(db_column='misuAmt', max_digits=12, decimal_places=0, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_misu'


class TblMngJaroe(models.Model):
    seq_no = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS')
    work_yy = models.CharField(db_column='work_YY', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    work_mm = models.IntegerField(db_column='work_MM')  # Field name made lowercase.
    yn_1 = models.CharField(db_column='YN_1', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_2 = models.CharField(db_column='YN_2', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_3 = models.CharField(db_column='YN_3', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_4 = models.CharField(db_column='YN_4', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_5 = models.CharField(db_column='YN_5', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_6 = models.CharField(db_column='YN_6', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_7 = models.CharField(db_column='YN_7', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_8 = models.CharField(db_column='YN_8', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_9 = models.CharField(db_column='YN_9', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_10 = models.CharField(db_column='YN_10', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_11 = models.CharField(db_column='YN_11', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_12 = models.CharField(db_column='YN_12', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_13 = models.CharField(db_column='YN_13', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_14 = models.CharField(db_column='YN_14', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    bigo = models.TextField(db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_mng_jaroe'


class TblReport(models.Model):
    seq_no = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS')
    work_yy = models.CharField(db_column='work_YY', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    sales_ti = models.DecimalField(db_column='sales_TI', max_digits=18, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    sales_kita = models.DecimalField(db_column='sales_Kita', max_digits=18, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    sales_young = models.DecimalField(db_column='sales_Young', max_digits=18, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    sales_notax = models.DecimalField(db_column='sales_Notax', max_digits=18, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    sales_total = models.DecimalField(db_column='sales_Total', max_digits=18, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    cost_wonga = models.DecimalField(db_column='cost_Wonga', max_digits=18, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    cost_pay = models.DecimalField(db_column='cost_Pay', max_digits=18, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    cost_ilyoung = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    cost_free = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    cost_etc = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    cost_total = models.DecimalField(db_column='cost_Total', max_digits=18, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    benefit = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    ntax = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    surtax = models.DecimalField(max_digits=18, decimal_places=0, blank=True, null=True)
    totaltax = models.DecimalField(db_column='totalTax', max_digits=18, decimal_places=0, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_report'


class TblReportAdvice(models.Model):
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    work_yy = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS')
    enddate = models.CharField(db_column='EndDate', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    txtadvice = models.TextField(db_column='txtAdvice', db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_report_Advice'


class TblSayoup(models.Model):
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    work_yy = models.CharField(db_column='work_YY', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    yn_1 = models.CharField(db_column='YN_1', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_2 = models.CharField(db_column='YN_2', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_3 = models.CharField(db_column='YN_3', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_4 = models.CharField(db_column='YN_4', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_5 = models.CharField(db_column='YN_5', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_6 = models.CharField(db_column='YN_6', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_7 = models.CharField(db_column='YN_7', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_8 = models.CharField(db_column='YN_8', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_9 = models.CharField(db_column='YN_9', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_sayoup'



class TblSheet(models.Model):
    seq = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    filename = models.CharField(db_column='fileName', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    sheetnum = models.CharField(db_column='sheetNum', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    sheetname = models.CharField(db_column='sheetName', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_sheet'


class TblSheetIncome(models.Model):
    seq = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    filename = models.CharField(db_column='fileName', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    sheetnum = models.CharField(db_column='sheetNum', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    sheetname = models.CharField(db_column='sheetName', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_sheet_income'


class TblSheetVat(models.Model):
    seq = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    filename = models.CharField(db_column='fileName', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    sheetnum = models.CharField(db_column='sheetNum', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    sheetname = models.CharField(db_column='sheetName', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_sheet_vat'


class TblVat(models.Model):
    seq_no = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    work_yy = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    work_qt = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    yn_1 = models.CharField(db_column='YN_1', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_2 = models.CharField(db_column='YN_2', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_3 = models.CharField(db_column='YN_3', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_4 = models.CharField(db_column='YN_4', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_5 = models.CharField(db_column='YN_5', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_6 = models.CharField(db_column='YN_6', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_7 = models.CharField(db_column='YN_7', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_8 = models.CharField(db_column='YN_8', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_9 = models.CharField(db_column='YN_9', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_10 = models.CharField(db_column='YN_10', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_11 = models.CharField(db_column='YN_11', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_12 = models.DecimalField(db_column='YN_12', max_digits=9, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    yn_13 = models.CharField(db_column='YN_13', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_14 = models.DecimalField(db_column='YN_14', max_digits=9, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    yn_15 = models.DecimalField(db_column='YN_15', max_digits=9, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    yn_16 = models.DecimalField(db_column='YN_16', max_digits=9, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    yn_17 = models.DecimalField(db_column='YN_17', max_digits=12, decimal_places=0, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_vat'


class TblVatkisu(models.Model):
    work_qt = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    skgb = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_vatKisu'


class TblVisit(models.Model):
    seq_no = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS')
    work_yy = models.CharField(db_column='work_YY', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    work_mm = models.CharField(db_column='work_MM', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    will_visit_dt = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_visit'


class TblWorkmanager(models.Model):
    seq_no = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS')
    work_dt = models.CharField(max_length=11, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    work_content = models.CharField(max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    work_check = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    work_input_dt = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tbl_workManager'


class TblYounmal(models.Model):
    seq_no = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    work_yy = models.CharField(db_column='work_YY', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    yn_1 = models.CharField(db_column='YN_1', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_2 = models.CharField(db_column='YN_2', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_3 = models.CharField(db_column='YN_3', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_4 = models.CharField(db_column='YN_4', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_5 = models.CharField(db_column='YN_5', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_6 = models.CharField(db_column='YN_6', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_7 = models.CharField(db_column='YN_7', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_8 = models.CharField(db_column='YN_8', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_9 = models.CharField(db_column='YN_9', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    yn_10 = models.CharField(db_column='YN_10', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tbl_younmal'


class Tblmuom(models.Model):
    uom = models.CharField(db_column='Uom', primary_key=True, max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    nama = models.CharField(db_column='Nama', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    keterangan = models.CharField(db_column='Keterangan', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    createdby = models.CharField(db_column='CreatedBy', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    createddate = models.DateTimeField(db_column='CreatedDate', blank=True, null=True)  # Field name made lowercase.
    lastupdatedby = models.CharField(db_column='LastUpdatedBy', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    lastupdateddate = models.DateTimeField(db_column='LastUpdatedDate', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tblmuom'


class TempAaa(models.Model):
    dt = models.CharField(max_length=8, db_collation='Korean_Wansung_CI_AS')
    gb = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS')
    price = models.IntegerField()
    amount = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'temp_aaa'


class TmpBs22(models.Model):
    gb = models.CharField(db_column='GB', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='ACNT_CD', max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    prt_nm = models.CharField(db_column='PRT_NM', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    tot_amt = models.DecimalField(db_column='TOT_AMT', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    prt_ord = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tmp_BS22'


class TmpBs333(models.Model):
    gb = models.CharField(db_column='GB', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='ACNT_CD', max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    prt_nm = models.CharField(db_column='PRT_NM', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    tot_amt = models.DecimalField(db_column='TOT_AMT', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    prt_ord = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tmp_BS333'


class TmpChk0318(models.Model):
    seq_no = models.CharField(db_column='Seq_No', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_acntcd = models.CharField(db_column='Financial_AcntCd', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_acntnm = models.CharField(db_column='Financial_AcntNm', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_trnacntnm = models.CharField(db_column='Financial_TrnAcntNm', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    debt_cr_ty = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tmp_CHK0318'


class TmpChk0609(models.Model):
    seq_no = models.CharField(db_column='Seq_No', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_acntcd = models.CharField(db_column='Financial_AcntCd', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_acntnm = models.CharField(db_column='Financial_AcntNm', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_trnacntnm = models.CharField(db_column='Financial_TrnAcntNm', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    debt_cr_ty = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tmp_CHK0609'


class TmpChk22(models.Model):
    seq_no = models.CharField(db_column='Seq_No', max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_acntcd = models.CharField(db_column='Financial_AcntCd', max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_acntnm = models.CharField(db_column='Financial_AcntNm', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    financial_trnacntnm = models.CharField(db_column='Financial_TrnAcntNm', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    debt_cr_ty = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tmp_CHK22'


class TmpCs0318(models.Model):
    gb = models.CharField(db_column='GB', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    chk_acnt = models.CharField(db_column='CHK_ACNT', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='ACNT_CD', max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    prt_nm = models.CharField(db_column='PRT_NM', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    tot_amt = models.DecimalField(db_column='TOT_AMT', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    prt_ord = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tmp_CS0318'


class TmpCs0609(models.Model):
    gb = models.CharField(db_column='GB', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    chk_acnt = models.CharField(db_column='CHK_ACNT', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='ACNT_CD', max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    prt_nm = models.CharField(db_column='PRT_NM', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    tot_amt = models.DecimalField(db_column='TOT_AMT', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    prt_ord = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tmp_CS0609'


class TmpCs222(models.Model):
    gb = models.CharField(db_column='GB', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='ACNT_CD', max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    prt_nm = models.CharField(db_column='PRT_NM', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    tot_amt = models.DecimalField(db_column='TOT_AMT', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    prt_ord = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tmp_CS_222'


class TmpPl(models.Model):
    gb = models.CharField(db_column='GB', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='ACNT_CD', max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    prt_nm = models.CharField(db_column='PRT_NM', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    tot_amt = models.DecimalField(db_column='TOT_AMT', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tmp_PL'


class TmpPl2(models.Model):
    gb = models.CharField(db_column='GB', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='ACNT_CD', max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    prt_nm = models.CharField(db_column='PRT_NM', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    tot_amt = models.DecimalField(db_column='TOT_AMT', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    prt_ord = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tmp_PL2'


class TmpPl20210209(models.Model):
    gb = models.CharField(db_column='GB', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='ACNT_CD', max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    prt_nm = models.CharField(db_column='PRT_NM', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    tot_amt = models.DecimalField(db_column='TOT_AMT', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    prt_ord = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tmp_PL20210209'


class TmpPrebs(models.Model):
    seq_no = models.CharField(db_column='Seq_No', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    work_yy = models.CharField(db_column='Work_YY', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='Acnt_cd', max_length=3, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_nm = models.CharField(db_column='Acnt_Nm', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_dt = models.CharField(db_column='Tran_Dt', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    remk = models.CharField(db_column='Remk', max_length=500, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_code = models.CharField(db_column='Trader_Code', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_name = models.CharField(db_column='Trader_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_bizno = models.CharField(db_column='Trader_Bizno', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    slip_no = models.CharField(db_column='Slip_No', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_stat = models.CharField(db_column='Tran_Stat', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crdr = models.CharField(db_column='CrDr', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tranamt_cr = models.DecimalField(db_column='TranAmt_Cr', max_digits=15, decimal_places=0)  # Field name made lowercase.
    tranamt_dr = models.DecimalField(db_column='TranAmt_Dr', max_digits=15, decimal_places=0)  # Field name made lowercase.
    employee_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    employee_name = models.CharField(db_column='employee_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    credit_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    credit_name = models.CharField(db_column='credit_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    place_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    place_name = models.CharField(db_column='place_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    project_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    project_name = models.CharField(db_column='project_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    cncl_dt = models.CharField(db_column='Cncl_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tmp_PreBS'


class TmpRe22(models.Model):
    gb = models.CharField(db_column='GB', max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='ACNT_CD', max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    prt_nm = models.CharField(db_column='PRT_NM', max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    tot_amt = models.DecimalField(db_column='TOT_AMT', max_digits=13, decimal_places=0, blank=True, null=True)  # Field name made lowercase.
    prt_ord = models.IntegerField(db_column='PRT_ORD', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tmp_RE22'


class TmpSlipledgrHcare(models.Model):
    seq_no = models.CharField(db_column='Seq_No', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    work_yy = models.CharField(db_column='Work_YY', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_cd = models.CharField(db_column='Acnt_cd', max_length=3, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    acnt_nm = models.CharField(db_column='Acnt_Nm', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_dt = models.CharField(db_column='Tran_Dt', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    remk = models.CharField(db_column='Remk', max_length=500, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_code = models.CharField(db_column='Trader_Code', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_name = models.CharField(db_column='Trader_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    trader_bizno = models.CharField(db_column='Trader_Bizno', max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    slip_no = models.CharField(db_column='Slip_No', max_length=5, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tran_stat = models.CharField(db_column='Tran_Stat', max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crdr = models.CharField(db_column='CrDr', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tranamt_cr = models.DecimalField(db_column='TranAmt_Cr', max_digits=15, decimal_places=0)  # Field name made lowercase.
    tranamt_dr = models.DecimalField(db_column='TranAmt_Dr', max_digits=15, decimal_places=0)  # Field name made lowercase.
    employee_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    employee_name = models.CharField(db_column='employee_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    credit_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    credit_name = models.CharField(db_column='credit_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    place_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    place_name = models.CharField(db_column='place_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    project_code = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS')
    project_name = models.CharField(db_column='project_Name', max_length=100, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    cncl_dt = models.CharField(db_column='Cncl_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    tid = models.CharField(max_length=32, db_collation='Korean_Wansung_CI_AS')

    class Meta:
        managed = False
        db_table = 'tmp_SlipLedgr_Hcare'


class Tmpslipledgr(models.Model):
    tran_dt = models.CharField(db_column='Tran_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    ibo_no = models.CharField(db_column='IBO_No', max_length=23, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    slip_no = models.CharField(db_column='Slip_No', max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tmpslipledgr'


class 면세전자신고(models.Model):
    자료명 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    wcd = models.CharField(db_column='wcD', max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    접수번호 = models.CharField(max_length=24, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    접수시각 = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    사업자번호 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    상호 = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    과세년월 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = '면세전자신고'


class 법인세전자신고(models.Model):
    제출년월 = models.CharField(max_length=12, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    과세년월 = models.CharField(max_length=12, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고구분 = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    상호 = models.CharField(max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    사업자등록번호 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    서식명 = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    조정구분 = models.CharField(max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    법인종류별구분 = models.CharField(max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    접수번호 = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    법인세_납부할세액 = models.FloatField(blank=True, null=True)
    법인세_분납세액 = models.FloatField(blank=True, null=True)
    법인세_차감세액 = models.FloatField(blank=True, null=True)
    농특세_분납세액 = models.FloatField(blank=True, null=True)
    농특세_차감세액 = models.FloatField(blank=True, null=True)
    농특세_충당세액 = models.FloatField(blank=True, null=True)
    주식변동여부 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    접수구분 = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    첨부서류 = models.CharField(max_length=5, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고시각 = models.CharField(max_length=16, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = '법인세전자신고'


class 법인세전자신고2(models.Model):
    과세년월 = models.CharField(max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고서종류 = models.CharField(max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고구분 = models.CharField(max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고유형 = models.CharField(max_length=6, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    상호 = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    사업자번호 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고번호 = models.CharField(max_length=25, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고시각 = models.CharField(max_length=40, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    접수여부 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = '법인세전자신고2'


class 법인세전자신고_Mid(models.Model):
    과세년월 = models.CharField(max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고서종류 = models.CharField(max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고구분 = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고유형 = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    상호 = models.CharField(max_length=150, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    사업자번호 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고번호 = models.CharField(max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고시각 = models.CharField(max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    접수여부 = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = '법인세전자신고_MID'


class 부가가치세전자신고(models.Model):
    no = models.FloatField(db_column='No', blank=True, null=True)  # Field name made lowercase.
    과세기간 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고구분 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    과세유형 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    환급구분 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    상호 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    사업자등록번호 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    접수여부 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    과세표준 = models.FloatField(blank=True, null=True)
    경감공제세액 = models.FloatField(blank=True, null=True)
    실제납부할세액 = models.FloatField(blank=True, null=True)
    매출세금계산서 = models.FloatField(blank=True, null=True)
    매입세금계산서 = models.FloatField(blank=True, null=True)
    기타매출 = models.FloatField(blank=True, null=True)
    기타매입 = models.FloatField(blank=True, null=True)
    면세매출 = models.FloatField(blank=True, null=True)
    면세매입 = models.FloatField(blank=True, null=True)
    영세율매출 = models.FloatField(blank=True, null=True)
    신고번호 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고시각 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = '부가가치세전자신고'


class 부가가치세전자신고3(models.Model):
    과세기간 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고구분 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    과세유형 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    환급구분 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    상호 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    사업자등록번호 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    접수여부 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고번호 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고시각 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    매출과세세금계산서발급금액 = models.FloatField(blank=True, null=True)
    매출과세세금계산서발급세액 = models.FloatField(blank=True, null=True)
    매출과세매입자발행세금계산서금액 = models.FloatField(blank=True, null=True)
    매출과세매입자발행세금계산서세액 = models.FloatField(blank=True, null=True)
    매출과세카드현금발행금액 = models.FloatField(blank=True, null=True)
    매출과세카드현금발행세액 = models.FloatField(blank=True, null=True)
    매출과세기타금액 = models.FloatField(blank=True, null=True)
    매출과세기타세액 = models.FloatField(blank=True, null=True)
    매출영세율세금계산서발급금액 = models.FloatField(blank=True, null=True)
    매출영세율기타금액 = models.FloatField(blank=True, null=True)
    매출예정누락합계금액 = models.FloatField(blank=True, null=True)
    매출예정누락합계세액 = models.FloatField(blank=True, null=True)
    예정누락매출세금계산서금액 = models.FloatField(blank=True, null=True)
    예정누락매출세금계산서세액 = models.FloatField(blank=True, null=True)
    예정누락매출과세기타금액 = models.FloatField(blank=True, null=True)
    예정누락매출과세기타세액 = models.FloatField(blank=True, null=True)
    예정누락매출영세율세금계산서금액 = models.FloatField(blank=True, null=True)
    예정누락매출영세율기타금액 = models.FloatField(blank=True, null=True)
    예정누락매출명세합계금액 = models.FloatField(blank=True, null=True)
    예정누락매출명세합계세액 = models.FloatField(blank=True, null=True)
    매출대손세액가감세액 = models.FloatField(blank=True, null=True)
    과세표준금액 = models.FloatField(blank=True, null=True)
    산출세액 = models.FloatField(blank=True, null=True)
    매입세금계산서수취일반금액 = models.FloatField(blank=True, null=True)
    매입세금계산서수취일반세액 = models.FloatField(blank=True, null=True)
    매입세금계산서수취고정자산금액 = models.FloatField(blank=True, null=True)
    매입세금계산서수취고정자산세액 = models.FloatField(blank=True, null=True)
    매입예정누락합계금액 = models.FloatField(blank=True, null=True)
    매입예정누락합계세액 = models.FloatField(blank=True, null=True)
    예정누락매입신고세금계산서금액 = models.FloatField(blank=True, null=True)
    예정누락매입신고세금계산서세액 = models.FloatField(blank=True, null=True)
    예정누락매입기타공제금액 = models.FloatField(blank=True, null=True)
    예정누락매입기타공제세액 = models.FloatField(blank=True, null=True)
    예정누락매입명세합계금액 = models.FloatField(blank=True, null=True)
    예정누락매입명세합계세액 = models.FloatField(blank=True, null=True)
    매입자발행세금계산서매입금액 = models.FloatField(blank=True, null=True)
    매입자발행세금계산서매입세액 = models.FloatField(blank=True, null=True)
    매입기타공제매입금액 = models.FloatField(blank=True, null=True)
    매입기타공제매입세액 = models.FloatField(blank=True, null=True)
    그밖의공제매입명세합계금액 = models.FloatField(blank=True, null=True)
    그밖의공제매입명세합계세액 = models.FloatField(blank=True, null=True)
    매입세액합계금액 = models.FloatField(blank=True, null=True)
    매입세액합계세액 = models.FloatField(blank=True, null=True)
    공제받지못할매입합계금액 = models.FloatField(blank=True, null=True)
    공제받지못할매입합계세액 = models.FloatField(blank=True, null=True)
    공제받지못할매입금액 = models.FloatField(blank=True, null=True)
    공제받지못할매입세액 = models.FloatField(blank=True, null=True)
    공제받지못할공통매입면세사업금액 = models.FloatField(blank=True, null=True)
    공제받지못할공통매입면세사업세액 = models.FloatField(blank=True, null=True)
    공제받지못할대손처분금액 = models.FloatField(blank=True, null=True)
    공제받지못할대손처분세액 = models.FloatField(blank=True, null=True)
    공제받지못할매입명세합계금액 = models.FloatField(blank=True, null=True)
    공제받지못할매입명세합계세액 = models.FloatField(blank=True, null=True)
    차감합계금액 = models.FloatField(blank=True, null=True)
    차감합계세액 = models.FloatField(blank=True, null=True)
    납부환급세액 = models.FloatField(blank=True, null=True)
    그밖의경감공제세액 = models.FloatField(blank=True, null=True)
    그밖의경감공제명세합계세액 = models.FloatField(blank=True, null=True)
    경감공제합계세액 = models.FloatField(blank=True, null=True)
    예정신고미환급세액 = models.FloatField(blank=True, null=True)
    예정고지세액 = models.FloatField(blank=True, null=True)
    사업양수자의대리납부기납부세액 = models.FloatField(blank=True, null=True)
    매입자납부특례기납부세액 = models.FloatField(blank=True, null=True)
    가산세액계 = models.FloatField(blank=True, null=True)
    차감납부할세액 = models.FloatField(blank=True, null=True)
    과세표준명세수입금액제외금액 = models.FloatField(blank=True, null=True)
    과세표준명세합계수입금액 = models.FloatField(blank=True, null=True)
    면세사업수입금액제외금액 = models.FloatField(blank=True, null=True)
    면세사업합계수입금액 = models.FloatField(blank=True, null=True)
    계산서교부금액 = models.FloatField(blank=True, null=True)
    계산서수취금액 = models.FloatField(blank=True, null=True)
    환급구분코드 = models.CharField(max_length=2, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    은행코드 = models.CharField(max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    계좌번호 = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    총괄납부승인번호 = models.CharField(max_length=9, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    은행지점명 = models.CharField(max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    폐업일자 = models.CharField(max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    폐업사유 = models.CharField(max_length=3, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    기한후여부 = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    실차감납부할세액 = models.FloatField(blank=True, null=True)
    일반과세자구분 = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    조기환급취소구분 = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    수출기업수입납부유예 = models.FloatField(blank=True, null=True)
    업종코드 = models.CharField(max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    전자외매출세금계산서 = models.TextField(db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    전자외매출세금계산서합계 = models.TextField(db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    전자외매입세금계산서 = models.TextField(db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    전자외매입세금계산서합계 = models.TextField(db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    inspect_issue = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    inspect_elec = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    inspect_labor = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신용카드발행집계표 = models.CharField(max_length=250, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신용카드수취기타카드 = models.CharField(max_length=140, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신용카드수취현금영수증 = models.CharField(max_length=140, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신용카드수취화물복지 = models.CharField(max_length=140, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신용카드수취사업용카드 = models.CharField(max_length=140, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    공제받지못할매입세액명세 = models.CharField(max_length=210, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = '부가가치세전자신고3'


class 부가가치세통합조회(models.Model):
    과세기수 = models.CharField(max_length=8, db_collation='Korean_Wansung_CI_AS')
    과세기간 = models.CharField(max_length=22, db_collation='Korean_Wansung_CI_AS')
    신고구분 = models.CharField(max_length=3, db_collation='Korean_Wansung_CI_AS')
    사업자등록번호 = models.CharField(max_length=12, db_collation='Korean_Wansung_CI_AS')
    상호 = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS')
    신고유형 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS')
    법인예정고지대상 = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS')
    관할서 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS')
    주업종코드 = models.CharField(max_length=8, db_collation='Korean_Wansung_CI_AS')
    간이부가율 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS')
    매출전자세금계산서공급가액 = models.DecimalField(max_digits=18, decimal_places=0)
    매출전자세금계산서세액 = models.DecimalField(max_digits=18, decimal_places=0)
    매출전자계산서공급가액 = models.DecimalField(max_digits=18, decimal_places=0)
    매출신용카드공급가액 = models.DecimalField(max_digits=18, decimal_places=0)
    매출신용카드세액 = models.DecimalField(max_digits=18, decimal_places=0)
    매출현금영수증공급가액 = models.DecimalField(max_digits=18, decimal_places=0)
    매출현금영수증세액 = models.DecimalField(max_digits=18, decimal_places=0)
    수출신고필증 = models.DecimalField(max_digits=18, decimal_places=0)
    구매확인서등 = models.DecimalField(max_digits=18, decimal_places=0)
    매입전자세금계산서공급가액 = models.DecimalField(max_digits=18, decimal_places=0)
    매입전자세금계산서세액 = models.DecimalField(max_digits=18, decimal_places=0)
    매입전자계산서공급가액 = models.DecimalField(max_digits=18, decimal_places=0)
    매입신용카드공급가액 = models.DecimalField(max_digits=18, decimal_places=0)
    매입신용카드세액 = models.DecimalField(max_digits=18, decimal_places=0)
    매입현금영수증공급가액 = models.DecimalField(max_digits=18, decimal_places=0)
    매입현금영수증세액 = models.DecimalField(max_digits=18, decimal_places=0)
    매입복지카드공급가액 = models.DecimalField(max_digits=18, decimal_places=0)
    매입복지카드세액 = models.DecimalField(max_digits=18, decimal_places=0)
    예정고지세액일반 = models.DecimalField(max_digits=18, decimal_places=0)
    예정미환급세액일반 = models.DecimalField(max_digits=18, decimal_places=0)
    예정부과세액간이 = models.DecimalField(max_digits=18, decimal_places=0)
    예정신고세액간이 = models.DecimalField(max_digits=18, decimal_places=0)
    매입자납부특례기납부세액 = models.DecimalField(max_digits=18, decimal_places=0)
    현금매출명세서 = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS')
    부동산임대공급가액명세서 = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS')

    class Meta:
        managed = False
        db_table = '부가가치세통합조회'


class 원천세전자신고(models.Model):
    과세연월 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고서종류 = models.CharField(max_length=22, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고구분 = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고유형 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    상호 = models.CharField(max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    사업자등록번호 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    접수일시 = models.CharField(max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    접수번호 = models.CharField(max_length=25, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    접수여부 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    지급연월 = models.CharField(max_length=6, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    제출연월 = models.CharField(max_length=6, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    a01 = models.FloatField(db_column='A01', blank=True, null=True)  # Field name made lowercase.
    a20 = models.FloatField(db_column='A20', blank=True, null=True)  # Field name made lowercase.
    a30 = models.FloatField(db_column='A30', blank=True, null=True)  # Field name made lowercase.
    a40 = models.FloatField(db_column='A40', blank=True, null=True)  # Field name made lowercase.
    a50 = models.FloatField(db_column='A50', blank=True, null=True)  # Field name made lowercase.
    a99 = models.FloatField(db_column='A99', blank=True, null=True)  # Field name made lowercase.
    작성일자 = models.CharField(max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    a01m = models.FloatField(db_column='A01M', blank=True, null=True)  # Field name made lowercase.
    a20m = models.FloatField(db_column='A20M', blank=True, null=True)  # Field name made lowercase.
    a30m = models.FloatField(db_column='A30M', blank=True, null=True)  # Field name made lowercase.
    a40m = models.FloatField(db_column='A40M', blank=True, null=True)  # Field name made lowercase.
    a50m = models.FloatField(db_column='A50M', blank=True, null=True)  # Field name made lowercase.
    a99m = models.FloatField(db_column='A99M', blank=True, null=True)  # Field name made lowercase.
    a03 = models.FloatField(blank=True, null=True)
    a03m = models.FloatField(blank=True, null=True)
    a60 = models.FloatField(db_column='A60', blank=True, null=True)  # Field name made lowercase.
    a60m = models.FloatField(db_column='A60M', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = '원천세전자신고'


class 의사정보(models.Model):
    no = models.FloatField(db_column='NO', blank=True, null=True)  # Field name made lowercase.
    taxid = models.CharField(db_column='TAXID', max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    dname = models.CharField(db_column='DNAME', max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    gcode = models.CharField(db_column='GCODE', max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    dcode = models.CharField(db_column='DCODE', max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    주소 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    hname = models.CharField(db_column='HNAME', max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    addr = models.CharField(db_column='ADDR', max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.
    tel = models.CharField(db_column='TEL', max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = '의사정보'


class 일용직전자신고(models.Model):
    번호 = models.IntegerField(blank=True, null=True)
    사업자등록번호 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    상호 = models.CharField(max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    과세년월 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    제출건수 = models.IntegerField(blank=True, null=True)
    총금액 = models.FloatField(blank=True, null=True)
    접수일시 = models.CharField(max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    접수번호 = models.CharField(max_length=25, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = '일용직전자신고'

class 전자세금계산서스크래핑관리(models.Model):
    crt_dt = models.CharField(db_column='crt_dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  
    seqno_lastTry = models.CharField(db_column='seqno_lastTry', max_length=5, db_collation='Korean_Wansung_CI_AS')  
    class Meta:
        managed = False
        db_table = '전자세금계산서스크래핑관리'

class 전자세금계산서(models.Model):
    seq_no = models.CharField(db_column='SEQ_NO', primary_key=True, max_length=4, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    사업자번호 = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS')
    매입매출구분 = models.CharField(max_length=1, db_collation='Korean_Wansung_CI_AS')
    작성일자 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS')
    승인번호 = models.CharField(max_length=30, db_collation='Korean_Wansung_CI_AS')
    발급일자 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS')
    전송일자 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS')
    공급자사업자등록번호 = models.CharField(max_length=12, db_collation='Korean_Wansung_CI_AS')
    공급자상호 = models.CharField(max_length=30, db_collation='Korean_Wansung_CI_AS')
    공급자대표자명 = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS')
    공급자주소 = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS')
    공급받는자사업자등록번호 = models.CharField(max_length=12, db_collation='Korean_Wansung_CI_AS')
    공급받는자상호 = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS')
    공급받는자대표자명 = models.CharField(max_length=30, db_collation='Korean_Wansung_CI_AS')
    공급받는자주소 = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS')
    합계금액 = models.DecimalField(max_digits=15, decimal_places=0)
    공급가액 = models.DecimalField(max_digits=15, decimal_places=0)
    세액 = models.DecimalField(max_digits=15, decimal_places=0)
    전자세금계산서분류 = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS')
    전자세금계산서종류 = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS')
    발급유형 = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS')
    비고 = models.CharField(max_length=50, db_collation='Korean_Wansung_CI_AS')
    영수청구구분 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS')
    공급자이메일 = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS')
    공급받는자이메일1 = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS')
    공급받는자이메일2 = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS')
    품목일자 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS')
    품목명 = models.CharField(max_length=300, db_collation='Korean_Wansung_CI_AS')
    품목규격 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS')
    품목수량 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS')
    품목단가 = models.DecimalField(max_digits=15, decimal_places=0)
    품목공급가액 = models.DecimalField(max_digits=15, decimal_places=0)
    품목세액 = models.DecimalField(max_digits=15, decimal_places=0)
    품목비고 = models.CharField(max_length=300, db_collation='Korean_Wansung_CI_AS')
    crt_dt = models.CharField(db_column='Crt_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    slip_dt = models.CharField(db_column='Slip_Dt', max_length=8, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    slip_acnt_cd = models.CharField(db_column='Slip_Acnt_Cd', max_length=10, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.
    slip_yn = models.CharField(db_column='Slip_YN', max_length=1, db_collation='Korean_Wansung_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = '전자세금계산서'
        unique_together = (('seq_no', '사업자번호', '매입매출구분', '승인번호'),)

class 종합소득세전자신고(models.Model):
    no = models.FloatField(db_column='No', blank=True, null=True)  # Field name made lowercase.
    귀속년도 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고유형 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    성명 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    주민등록번호 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고번호 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    소득세과세표준 = models.FloatField(blank=True, null=True)
    소득세산출세액 = models.FloatField(blank=True, null=True)
    소득세납부할총세액 = models.FloatField(blank=True, null=True)
    지방세과세표준 = models.FloatField(blank=True, null=True)
    지방세산출세액 = models.FloatField(blank=True, null=True)
    지방세납부할총세액 = models.FloatField(blank=True, null=True)
    농특세과세표준 = models.FloatField(blank=True, null=True)
    농특세산출세액 = models.FloatField(blank=True, null=True)
    농특세납부할총세액 = models.FloatField(blank=True, null=True)
    접수구분 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    구비서류 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고시각 = models.CharField(max_length=255, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = '종합소득세전자신고'


class 종합소득세전자신고2(models.Model):
    과세년월 = models.CharField(max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고서종류 = models.CharField(max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고구분 = models.CharField(max_length=8, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고유형 = models.CharField(max_length=6, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    이름 = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    주민번호 = models.CharField(max_length=15, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고시각 = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고번호 = models.CharField(max_length=25, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    접수여부 = models.CharField(max_length=10, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = '종합소득세전자신고2'


class 지급조서간이소득(models.Model):
    신고서종류 = models.CharField(max_length=40, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    사업자번호 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    상호 = models.CharField(max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    과세년도 = models.CharField(max_length=6, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고구분 = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    접수자 = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    제출건수 = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    제출금액 = models.FloatField(blank=True, null=True)
    접수일시 = models.CharField(max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    접수번호 = models.CharField(max_length=25, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    작성일자 = models.CharField(max_length=25, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = '지급조서간이소득'


class 지급조서전자신고(models.Model):
    신고서종류 = models.CharField(max_length=40, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    사업자번호 = models.CharField(max_length=13, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    상호 = models.CharField(max_length=50, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    과세년도 = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    신고구분 = models.CharField(max_length=20, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    접수자 = models.CharField(max_length=100, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    제출건수 = models.CharField(max_length=4, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    제출금액 = models.FloatField(blank=True, null=True)
    접수일시 = models.CharField(max_length=30, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    접수번호 = models.CharField(max_length=25, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)
    작성일자 = models.CharField(max_length=25, db_collation='Korean_Wansung_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = '지급조서전자신고'




# 블로그 작성 관련
class BlogCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name


class BlogAuthor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='blog_author')
    bio = models.TextField(blank=True, null=True)
    profile_pic = models.ImageField(upload_to='blog_authors_pics/', null=True, blank=True)

    def __str__(self):
        return self.user.username


class BlogPost(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(BlogAuthor, on_delete=models.CASCADE, related_name='blogposts')
    is_public = models.BooleanField(default=True)
    published_date = models.DateTimeField(auto_now_add=True)
    views = models.IntegerField(default=0)  # 조회수
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)  # 좋아요 누른 사용자
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='blog_posts')
    new_law = models.BooleanField(default=False)
    youtube_url = models.URLField(blank=True)
    important_grade = models.CharField(max_length=20, choices=[('1', '매우중요'), ('2', '중요'), ('3', '기본'), ('4', '상식')], default='3')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog_detail', kwargs={'pk': self.id})

    
class BlogComment(models.Model):
    post = models.ForeignKey(BlogPost, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', related_name='replies', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"   

class BlogPostAttachment(models.Model):
    post = models.ForeignKey(BlogPost, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to='blog_post_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.post.title} uploaded at {self.uploaded_at}"
