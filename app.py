import os, sqlite3, secrets, hmac, uuid
from functools import wraps
from flask import Flask, request, session, redirect, url_for, render_template_string, abort, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
app=Flask(__name__)
app.secret_key=os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',SESSION_COOKIE_SECURE=os.environ.get('HTTPS')=='1')
DB=os.environ.get('DB_PATH','pt.sqlite3')
STATES=['Chờ thanh toán','Chờ xác nhận','Đã thanh toán','Đang xử lý','Chờ bàn giao','Hoàn thành','Đã hủy']
def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
with db() as c:
    c.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password TEXT, role TEXT); CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY, uid INTEGER, page TEXT, qty INTEGER, price INTEGER, cost INTEGER, commission INTEGER, status TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP, link TEXT DEFAULT '', finished TEXT); CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY,price INTEGER,cost INTEGER,commission INTEGER); INSERT OR IGNORE INTO settings VALUES(1,790000,0,0); CREATE TABLE IF NOT EXISTS logs(id INTEGER PRIMARY KEY, actor TEXT, action TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP);''')
    pw=os.environ.get('ADMIN_PASSWORD'); email=os.environ.get('ADMIN_EMAIL','admin@ptagency.local')
    if pw and len(pw)>=12: c.execute('INSERT OR IGNORE INTO users(name,email,password,role) VALUES(?,?,?,?)',('PT Agency Admin',email.lower(),generate_password_hash(pw),'admin'))
def user():
    with db() as c: return c.execute('SELECT * FROM users WHERE id=?',(session.get('uid',0),)).fetchone()
def guard(admin=False):
    def deco(f):
        @wraps(f)
        def wrapper(*a,**k):
            u=user()
            if not u: return redirect('/login')
            if admin and u['role']!='admin': abort(403)
            return f(*a,**k)
        return wrapper
    return deco
@app.before_request
def csrf():
    if 'csrf' not in session: session['csrf']=secrets.token_hex(24)
    if request.method=='POST' and not hmac.compare_digest(session['csrf'],request.form.get('csrf','')): abort(400)
@app.context_processor
def common(): return dict(u=user(),csrf=session['csrf'],money=lambda n:f'{n:,}'.replace(',','.')+'đ',states=STATES)
BASE='''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>PT Agency V2.0</title><style>*{box-sizing:border-box}body{margin:0;background:#080f20;color:#e8f1ff;font:15px system-ui}a{color:#68c9ff;text-decoration:none}header{display:flex;align-items:center;gap:16px;flex-wrap:wrap;padding:15px 5%;border-bottom:1px solid #263a56;background:#101b30}header img{width:48px;border-radius:50%}header strong{font-size:22px;color:#52c4ff;margin-right:auto}main{max-width:1250px;margin:auto;padding:32px 20px}h1{font-size:clamp(30px,5vw,55px);line-height:1.12}h2,h3{margin-top:0}p{color:#a8bcd8;line-height:1.65}.panel{background:#101d33;border:1px solid #293e60;border-radius:16px;padding:24px;margin-bottom:16px}.hero{display:grid;grid-template-columns:1.4fr 1fr;gap:30px;align-items:center;background:radial-gradient(ellipse at right,#153b78,#101d33)}.hero img{width:min(100%,330px);border-radius:50%;box-shadow:0 0 45px #007aff66;margin:auto}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px}.metric{font-size:27px;color:#60caff;font-weight:bold}.btn,button{display:inline-block;background:#1174e8;border:1px solid #369aff;color:white;padding:11px 17px;border-radius:9px;font:inherit;cursor:pointer}input,select{width:100%;background:#080f20;color:#fff;border:1px solid #344c70;padding:11px;border-radius:8px;margin:6px 0 14px;font:inherit}label{color:#a9c4e4}form{margin:0}.shell{display:grid;grid-template-columns:190px minmax(0,1fr);gap:22px}aside a{display:block;padding:13px;border-bottom:1px solid #243954}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;min-width:650px}td,th{text-align:left;padding:12px;border-bottom:1px solid #283b57}small{color:#9bb3d0}.note{background:#132c4d;border-radius:8px;padding:12px}footer{text-align:center;padding:20px;color:#8298b5}@media(max-width:700px){.hero,.shell{grid-template-columns:1fr}aside{display:flex;flex-wrap:wrap}main{padding:18px 12px}}</style><header><img src="/logo"><strong>PT AGENCY</strong><a href="/">Trang chủ</a>{% if u %}<a href="/orders">Đơn của tôi</a>{% if u.role=='admin' %}<a href="/admin">Admin</a>{% endif %}<form method="post" action="/logout"><input type="hidden" name="csrf" value="{{csrf}}"><button>Đăng xuất</button></form>{% else %}<a href="/login">Đăng nhập</a><a href="/register">Đăng ký</a>{% endif %}</header><main>BODY</main><footer>PT Agency · V2.0 · Chưa tích hợp ngân hàng hoặc Meta</footer></html>'''
def page(body,**kw): return render_template_string(BASE.replace('BODY',body),**kw)
F='<input type="hidden" name="csrf" value="{{csrf}}">'
@app.get('/logo')
def logo(): return send_from_directory(app.root_path,'logo.webp')
@app.get('/')
def home():
    with db() as c: s=c.execute('SELECT * FROM settings').fetchone()
    return page('''<div class="panel hero"><div><small> DIGITAL BRAND SOLUTIONS </small><h1>Giải pháp <span style="color:#57caff">Tick Xanh</span> Fanpage chuyên nghiệp</h1><p>Khởi tạo Fanpage mới · Bảo hành 12 tháng</p><div class="metric">{{money(s.price)}} / Page</div><p><a class="btn" href="/orders">Đặt dịch vụ ngay</a></p></div><img src="/logo"></div><div class="grid"><div class="panel"><h3>Khởi tạo mới</h3><p>Không nhận Page có sẵn.</p></div><div class="panel"><h3>Thanh toán trước</h3><p>Xác nhận thủ công sau đối soát.</p></div><div class="panel"><h3>Theo dõi tiến độ</h3><p>Quản lý đơn hàng theo tài khoản.</p></div></div><p>Xác minh phụ thuộc điều kiện của Meta. PT Agency không phải đại diện chính thức của Meta.</p>''',s=s)
@app.route('/login',methods=['GET','POST'])
@app.route('/register',methods=['GET','POST'])
def auth():
    reg=request.path=='/register'; error=''
    if request.method=='POST':
        email=request.form.get('email','').strip().lower(); pw=request.form.get('password',''); name=request.form.get('name','').strip()
        with db() as c:
            if reg:
                if not name or '@' not in email or len(pw)<12: error='Nhập đủ thông tin và mật khẩu ít nhất 12 ký tự.'
                else:
                    try: c.execute('INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)',(name,email,generate_password_hash(pw),'customer')); return redirect('/login')
                    except sqlite3.IntegrityError: error='Không thể đăng ký email này.'
            else:
                u=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
                if u and check_password_hash(u['password'],pw): session.clear(); session['uid']=u['id']; return redirect('/admin' if u['role']=='admin' else '/orders')
                error='Thông tin đăng nhập không đúng.'
    return page('<div class="panel" style="max-width:450px;margin:auto"><h2>{{"Đăng ký" if reg else "Đăng nhập"}}</h2><p>{{error}}</p><form method="post">'+F+'{% if reg %}<label>Họ tên</label><input name="name" required>{% endif %}<label>Email</label><input type="email" name="email" required><label>Mật khẩu</label><input type="password" name="password" required><button>Tiếp tục</button></form></div>',reg=reg,error=error)
@app.post('/logout')
def logout(): session.clear(); return redirect('/')
@app.route('/orders',methods=['GET','POST'])
@guard()
def orders():
    u=user()
    with db() as c:
        s=c.execute('SELECT * FROM settings').fetchone()
        if request.method=='POST':
            try: qty=int(request.form['qty']); assert 1<=qty<=100
            except (ValueError,KeyError,AssertionError): abort(400)
            name=request.form.get('page','').strip()
            if not name or len(name)>250: abort(400)
            c.execute('INSERT INTO orders(id,uid,page,qty,price,cost,commission,status) VALUES(?,?,?,?,?,?,?,?)',('PT-'+uuid.uuid4().hex[:12].upper(),u['id'],name,qty,s['price'],s['cost'],s['commission'],STATES[0])); return redirect('/orders')
        rows=c.execute('SELECT * FROM orders WHERE uid=? ORDER BY created DESC',(u['id'],)).fetchall()
    return page('<h2>Đơn hàng của tôi</h2><div class="panel"><h3>Đặt Fanpage mới</h3><form method="post">'+F+'<label>Tên Fanpage</label><input name="page" required maxlength="250"><label>Số lượng</label><input type="number" min="1" max="100" value="1" name="qty" id="qty" oninput="document.getElementById(\'sum\').textContent=(this.value*{{s.price}}).toLocaleString(\'vi-VN\')+\'đ\'" required><p>Tổng tiền: <b id="sum">{{money(s.price)}}</b></p><button>Tạo đơn</button></form><p class="note">Chưa cấu hình tài khoản ngân hàng. Không chuyển tiền tại bản thử nghiệm.</p></div>{% for o in rows %}<div class="panel"><b>{{o.id}} · {{o.status}}</b><h3>{{o.page}}</h3><p>{{money(o.qty*o.price)}} · {{o.qty}} Page</p>{% if o.status==states[0] %}<form method="post" action="/notify/{{o.id}}">'+F+'<button>Thông báo đã chuyển khoản (thử nghiệm)</button></form>{% endif %}{% if o.link %}<p>Link bàn giao: {{o.link}}</p>{% endif %}</div>{% endfor %}',rows=rows,s=s)
@app.post('/notify/<oid>')
@guard()
def notify(oid):
    with db() as c: c.execute('UPDATE orders SET status=? WHERE id=? AND uid=? AND status=?',(STATES[1],oid,user()['id'],STATES[0]))
    return redirect('/orders')
@app.route('/admin',methods=['GET','POST'])
@guard(True)
def admin():
    with db() as c:
        if request.method=='POST':
            action=request.form.get('action'); actor=user()['email']
            if action=='settings':
                try: vals=[int(request.form[k]) for k in ('price','cost','commission')]; assert all(0<=v<=10**9 for v in vals) and vals[0]>0
                except (ValueError,KeyError,AssertionError): abort(400)
                c.execute('UPDATE settings SET price=?,cost=?,commission=? WHERE id=1',vals)
            elif action=='update':
                oid=request.form.get('oid'); status=request.form.get('status'); link=request.form.get('link','')[:500]; o=c.execute('SELECT * FROM orders WHERE id=?',(oid,)).fetchone()
                if not o or status not in STATES: abort(400)
                allowed={0:[1,2,6],1:[0,2,6],2:[3],3:[4],4:[5],5:[],6:[]}; old=STATES.index(o['status']); new=STATES.index(status)
                if new!=old and new not in allowed[old]: abort(400,'Không thể chuyển trạng thái này')
                if new==5 and not link: abort(400,'Cần link bàn giao')
                c.execute('UPDATE orders SET status=?,link=?,finished=CASE WHEN ?=5 THEN COALESCE(finished,CURRENT_TIMESTAMP) ELSE finished END WHERE id=?',(status,link,new,oid))
            else: abort(400)
            c.execute('INSERT INTO logs(actor,action) VALUES(?,?)',(actor,action+' '+request.form.get('oid',''))); return redirect('/admin')
        rows=c.execute('SELECT orders.*,users.name,users.email FROM orders JOIN users ON users.id=orders.uid ORDER BY created DESC').fetchall(); customers=c.execute("SELECT name,email FROM users WHERE role='customer'").fetchall(); s=c.execute('SELECT * FROM settings').fetchone(); logs=c.execute('SELECT * FROM logs ORDER BY id DESC LIMIT 50').fetchall()
    paid=[o for o in rows if o['status'] in STATES[2:6]]; done=[o for o in rows if o['status']==STATES[5]]
    return page('''<div class="shell"><aside class="panel"><h3>SUPER ADMIN</h3><a href="#overview">Tổng quan</a><a href="#list">Đơn hàng</a><a href="#customers">Khách hàng</a><a href="#settings">Giá & chi phí</a><a href="#logs">Nhật ký</a></aside><div><h2 id="overview">Bảng điều hành PT Agency</h2><div class="grid">{% for k,v in metrics %}<div class="panel"><small>{{k}}</small><div class="metric">{{v}}</div></div>{% endfor %}</div><div class="panel" id="list"><h3>Quản lý đơn hàng</h3><p>Xác nhận thanh toán chỉ sau khi đối chiếu ngân hàng. Bản thử nghiệm không tự xác nhận giao dịch.</p><div class="scroll"><table><tr><th>Đơn / Khách hàng</th><th>Fanpage / Tiền</th><th>Trạng thái & bàn giao</th></tr>{% for o in rows %}<tr><td>{{o.id}}<br>{{o.name}}<br><small>{{o.email}}</small></td><td>{{o.page}}<br>{{money(o.price*o.qty)}}</td><td><form method="post">'''+F+'''<input type="hidden" name="action" value="update"><input type="hidden" name="oid" value="{{o.id}}"><select name="status">{% for st in states %}<option {% if st==o.status %}selected{% endif %}>{{st}}</option>{% endfor %}</select><input name="link" placeholder="Link bàn giao" value="{{o.link}}"><button>Lưu</button></form>{% if o.finished %}<small>Bảo hành 12 tháng từ {{o.finished}}</small>{% endif %}</td></tr>{% endfor %}</table></div></div><div class="panel" id="customers"><h3>Khách hàng ({{customers|length}})</h3>{% for c in customers %}<p>{{c.name}} · {{c.email}}</p>{% endfor %}</div><div class="panel" id="settings"><h3>Giá bán & chi phí / Page</h3><form method="post">'''+F+'''<input type="hidden" name="action" value="settings"><div class="grid">{% for k,label in [('price','Giá bán'),('cost','Giá vốn'),('commission','Hoa hồng dự kiến')] %}<div><label>{{label}}</label><input name="{{k}}" type="number" min="0" value="{{s[k]}}" required></div>{% endfor %}</div><button>Lưu cấu hình</button></form><p>Giá vốn và hoa hồng mặc định 0, cần nhập thực tế. Chỉ áp dụng đơn mới.</p></div><div class="panel" id="logs"><h3>Nhật ký quản trị</h3>{% for l in logs %}<p>{{l.created}} · {{l.actor}} · {{l.action}}</p>{% endfor %}</div></div></div>''',rows=rows,customers=customers,s=s,logs=logs,metrics=[('Tổng đơn',len(rows)),('Tiền đã xác nhận',f"{sum(o['qty']*o['price'] for o in paid):,}đ"),('Hoàn thành',len(done)),('Lãi gộp dự kiến',f"{sum(o['qty']*(o['price']-o['cost']-o['commission']) for o in done):,}đ")])
if __name__=='__main__': app.run(host='127.0.0.1',port=8000)
