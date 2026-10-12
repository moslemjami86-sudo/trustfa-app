"""Seed default businesses."""
from models import Business

DEFAULT_BUSINESSES = [
    dict(name="دیجی‌کالا", category="فروشگاه اینترنتی", rating=4.6, reviews_count=12, logo="DK", color="bg-red-500", domain="digikala.com", icon="fa-shopping-cart", verified=True),
    dict(name="اسنپ", category="حمل‌ونقل", rating=4.3, reviews_count=8, logo="SN", color="bg-green-500", domain="snapp.ir", icon="fa-car", verified=True),
    dict(name="کافه‌بازار", category="نرم‌افزار", rating=4.8, reviews_count=5, logo="CB", color="bg-blue-500", domain="cafebazaar.ir", icon="fa-mobile-alt", verified=True),
    dict(name="بانک ملت", category="خدمات مالی", rating=3.9, reviews_count=3, logo="BM", color="bg-yellow-500", domain="bankmellat.ir", icon="fa-university", verified=True),
    dict(name="ایرانسل", category="مخابرات", rating=3.7, reviews_count=7, logo="IR", color="bg-yellow-400", domain="irancell.ir", icon="fa-signal", verified=True),
    dict(name="تپسی", category="حمل‌ونقل", rating=4.5, reviews_count=4, logo="TP", color="bg-orange-500", domain="tapsi.ir", icon="fa-taxi", verified=True),
    dict(name="آمازون", category="فروشگاه اینترنتی", rating=4.4, reviews_count=2, logo="AM", color="bg-slate-800", domain="amazon.com", icon="fa-box", verified=True),
    dict(name="اسنپ‌فود", category="رستوران و غذا", rating=4.2, reviews_count=9, logo="SF", color="bg-pink-500", domain="snappfood.ir", icon="fa-utensils", verified=True),
    dict(name="دیجی‌پی", category="خدمات مالی", rating=4.1, reviews_count=1, logo="DP", color="bg-indigo-500", domain="digipay.ir", icon="fa-wallet", verified=True),
    dict(name="همراه اول", category="مخابرات", rating=3.8, reviews_count=6, logo="HA", color="bg-blue-600", domain="mci.ir", icon="fa-phone", verified=True),
    dict(name="علی‌بابا", category="سفر", rating=4.0, reviews_count=0, logo="AB", color="bg-orange-600", domain="alibaba.ir", icon="fa-plane", verified=True),
    dict(name="جاباما", category="سفر", rating=4.3, reviews_count=1, logo="JB", color="bg-teal-500", domain="jabama.com", icon="fa-hotel", verified=True),
    dict(name="دیوار", category="نرم‌افزار", rating=4.5, reviews_count=11, logo="DW", color="bg-red-600", domain="divar.ir", icon="fa-bullhorn", verified=True),
    dict(name="شیپور", category="نرم‌افزار", rating=4.0, reviews_count=0, logo="SH", color="bg-purple-500", domain="sheypoor.com", icon="fa-tags", verified=True),
    dict(name="بانک سامان", category="خدمات مالی", rating=4.2, reviews_count=2, logo="BS", color="bg-cyan-600", domain="sb24.ir", icon="fa-landmark", verified=True),
    dict(name="مقداد آی‌تی", category="فروشگاه اینترنتی", rating=4.7, reviews_count=3, logo="MI", color="bg-emerald-600", domain="meghdadit.com", icon="fa-laptop", verified=True),
    dict(name="بیمه ایران", category="بیمه", rating=3.6, reviews_count=0, logo="BI", color="bg-green-700", domain="iraninsurance.ir", icon="fa-shield-alt", verified=True),
    dict(name="اسنپ‌دکتر", category="سلامت", rating=4.4, reviews_count=1, logo="SD", color="bg-rose-500", domain="snapp.doctor", icon="fa-user-md", verified=True),
    dict(name="فیدیبو", category="نرم‌افزار", rating=4.6, reviews_count=4, logo="FD", color="bg-amber-500", domain="fidibo.com", icon="fa-book", verified=True),
    dict(name="کافه بازار بازی", category="نرم‌افزار", rating=4.3, reviews_count=0, logo="CG", color="bg-violet-500", domain="cafebazaar.ir", icon="fa-gamepad", verified=True),
]


def seed_businesses(db):
    if db.query(Business).count() > 0:
        return
    for item in DEFAULT_BUSINESSES:
        db.add(Business(**item))
    db.commit()
