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
BASE='''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>PT Agency — Tick Xanh Fanpage</title><style>*{box-sizing:border-box}body{margin:0;background:#f8fafc;color:#0f172a;font:15px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}a{color:#2563eb;text-decoration:none}header{position:sticky;top:0;z-index:10;display:flex;align-items:center;gap:14px;flex-wrap:wrap;padding:12px 5%;background:#fff;border-bottom:1px solid #e2e8f0}header img{width:42px;height:42px;object-fit:cover;border-radius:12px}header strong{font-size:20px;letter-spacing:.4px;color:#0f172a;margin-right:auto}header a{color:#334155;font-weight:600;padding:8px 10px;border-radius:8px}header a:hover{background:#eff6ff;color:#2563eb}main{max-width:1120px;margin:auto;padding:40px 20px 56px}h1{font-size:clamp(32px,5vw,52px);line-height:1.15;margin:0 0 14px}h2{font-size:26px;margin:0 0 12px}h3{margin:0 0 8px;font-size:18px}p{color:#475569;line-height:1.7}.panel{background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:24px;margin-bottom:16px;box-shadow:0 1px 3px rgba(15,23,42,.05)}.hero{display:grid;grid-template-columns:1.25fr 1fr;gap:28px;align-items:stretch;background:#fff;border:1px solid #e2e8f0;border-radius:20px;padding:36px;box-shadow:0 8px 30px rgba(15,23,42,.06);margin-bottom:20px}.hero img{width:120px;height:120px;object-fit:cover;border-radius:50%;margin-bottom:14px}.eyebrow{display:inline-block;font-size:12px;font-weight:700;letter-spacing:1.5px;color:#2563eb;background:#eff6ff;border-radius:999px;padding:6px 12px;margin-bottom:14px}.price{font-size:36px;color:#2563eb;font-weight:800}.price small{font-size:15px;color:#64748b;font-weight:600}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px}.metric{font-size:26px;color:#0f172a;font-weight:800}.btn,button{display:inline-block;background:#2563eb;border:1px solid #2563eb;color:#fff;padding:11px 18px;border-radius:10px;font:inherit;font-weight:600;cursor:pointer}button:hover,.btn:hover{background:#1d4ed8}.btn-ghost{background:#fff;color:#2563eb;border:1px solid #bfdbfe}input,select{width:100%;background:#fff;color:#0f172a;border:1px solid #cbd5e1;padding:11px 12px;border-radius:10px;margin:6px 0 14px;font:inherit}input:focus,select:focus{outline:2px solid #bfdbfe;border-color:#2563eb}label{color:#334155;font-weight:600;font-size:14px}form{margin:0}.shell{display:grid;grid-template-columns:210px minmax(0,1fr);gap:22px;align-items:start}aside{position:sticky;top:78px}aside a{display:block;padding:11px 12px;border-radius:8px;color:#334155;font-weight:600}aside a:hover{background:#eff6ff;color:#2563eb}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;min-width:650px}td,th{text-align:left;padding:12px 10px;border-bottom:1px solid #e2e8f0;vertical-align:top}th{color:#64748b;font-size:13px;text-transform:uppercase;letter-spacing:.5px}small{color:#64748b}.note{background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:12px;color:#1e40af}.error{background:#fef2f2;border:1px solid #fecaca;color:#b91c1c;border-radius:10px;padding:12px;margin-bottom:14px}.badge{display:inline-block;font-size:12px;font-weight:700;padding:4px 10px;border-radius:999px}.badge-wait{background:#fef3c7;color:#92400e}.badge-proc{background:#dbeafe;color:#1d4ed8}.badge-done{background:#dcfce7;color:#166534}.badge-cancel{background:#fee2e2;color:#991b1b}.step-num{display:inline-flex;width:32px;height:32px;border-radius:50%;background:#2563eb;color:#fff;font-weight:700;align-items:center;justify-content:center;margin-bottom:10px}.check{color:#16a34a;font-weight:700}footer{text-align:center;padding:28px 20px;color:#64748b;border-top:1px solid #e2e8f0;background:#fff}@media(max-width:760px){.hero,.shell{grid-template-columns:1fr;padding:24px 18px}aside{position:static}main{padding:24px 14px 40px}header{padding:12px 14px}}</style><header><img src="/logo" alt="PT Agency"><strong>PT AGENCY</strong><a href="/">Trang chủ</a>{% if u %}<a href="/orders">Đơn của tôi</a>{% if u.role=='admin' %}<a href="/admin">Admin</a>{% endif %}<form method="post" action="/logout"><input type="hidden" name="csrf" value="{{csrf}}"><button>Đăng xuất</button></form>{% else %}<a href="/login">Đăng nhập</a><a href="/register">Đăng ký</a>{% endif %}</header><main>BODY</main><footer>PT Agency · Tick Xanh Fanpage · Zalo 0819 869 828<br><small>Chưa tích hợp ngân hàng hoặc Meta. Xác minh phụ thuộc điều kiện của Meta.</small></footer></html>'''
def page(body,**kw): return render_template_string(BASE.replace('BODY',body),**kw)
F='<input type="hidden" name="csrf" value="{{csrf}}">'
@app.get('/logo')
def logo(): return send_from_directory(app.root_path,'logo.webp')
@app.get('/')
def home():
    with db() as c: s=c.execute('SELECT * FROM settings').fetchone()
    return page('''<div class="hero"><div><span class="eyebrow">DIGITAL BRAND SOLUTIONS</span><h1>Giải pháp <span style="color:#2563eb">Tick Xanh</span> Fanpage chuyên nghiệp</h1><p>PT Agency khởi tạo Fanpage mới, hỗ trợ đăng ký xác minh Tick Xanh và bàn giao đầy đủ. Quy trình rõ ràng, theo dõi tiến độ từng đơn ngay trên tài khoản của bạn.</p><p><a class="btn" href="/orders">Đặt dịch vụ ngay</a> &nbsp; <a class="btn btn-ghost" href="/register">Tạo tài khoản</a></p><p><small>Liên hệ tư vấn: Zalo 0819 869 828</small></p></div><div class="panel" style="margin:0;text-align:center"><img src="/logo" alt="PT Agency"><div class="price">{{money(s.price)}} <small>/ Page</small></div><p style="margin:6px 0 16px">Giá trọn gói · Bảo hành 12 tháng</p><p style="text-align:left"><span class="check">✓</span> Khởi tạo Fanpage mới<br><span class="check">✓</span> Không nhận Page có sẵn<br><span class="check">✓</span> Thanh toán trước, xác nhận thủ công sau đối soát<br><span class="check">✓</span> Theo dõi tiến độ theo từng đơn</p><a class="btn" href="/orders">Đặt dịch vụ ngay</a></div></div><div class="grid"><div class="panel"><h3>Khởi tạo mới</h3><p>Không nhận Page có sẵn. Fanpage được tạo mới theo đúng tên và nhu cầu của bạn.</p></div><div class="panel"><h3>Bảo hành 12 tháng</h3><p>Bảo hành 12 tháng tính từ ngày bàn giao hoàn thành.</p></div><div class="panel"><h3>Theo dõi tiến độ</h3><p>Quản lý đơn hàng theo tài khoản, cập nhật trạng thái từng bước.</p></div></div><div class="panel"><h2>Quy trình 4 bước</h2><div class="grid"><div><span class="step-num">1</span><h3>Đặt đơn</h3><p>Đăng ký tài khoản, nhập tên Fanpage và số lượng cần làm.</p></div><div><span class="step-num">2</span><h3>Thanh toán</h3><p>Thanh toán trước theo hướng dẫn. Chưa tích hợp ngân hàng, xác nhận thủ công sau đối soát.</p></div><div><span class="step-num">3</span><h3>Xác nhận</h3><p>PT Agency đối soát và xác nhận đơn, sau đó bắt đầu xử lý.</p></div><div><span class="step-num">4</span><h3>Bàn giao</h3><p>Bàn giao Fanpage kèm link, bắt đầu tính bảo hành 12 tháng.</p></div></div></div><div class="panel"><h2>Câu hỏi thường gặp</h2><p><b>PT Agency có nhận Page có sẵn không?</b><br>Không. Dịch vụ chỉ khởi tạo Fanpage mới.</p><p><b>Tick Xanh có chắc chắn được duyệt không?</b><br>Không. Xác minh phụ thuộc điều kiện của Meta. PT Agency không phải đại diện chính thức của Meta.</p><p><b>Thanh toán như thế nào?</b><br>Thanh toán trước, PT Agency xác nhận thủ công sau khi đối soát. Chưa tích hợp ngân hàng, không chuyển tiền tự động trên web.</p><p><b>Cần hỗ trợ thì liên hệ đâu?</b><br>Zalo 0819 869 828.</p></div><p style="text-align:center"><a class="btn" href="/orders">Đặt dịch vụ ngay — {{money(s.price)}} / Page</a></p>''',s=s)
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
    return page('<div class="panel" style="max-width:460px;margin:32px auto"><div style="text-align:center;margin-bottom:8px"><img src="/logo" alt="PT Agency" style="width:72px;height:72px;object-fit:cover;border-radius:50%"></div><h2 style="text-align:center">{{"Đăng ký" if reg else "Đăng nhập"}}</h2><p style="text-align:center">{{"Tạo tài khoản để đặt dịch vụ Tick Xanh Fanpage." if reg else "Đăng nhập để quản lý đơn hàng của bạn."}}</p>{% if error %}<div class="error">{{error}}</div>{% endif %}<form method="post">'+F+'{% if reg %}<label>Họ tên</label><input name="name" required>{% endif %}<label>Email</label><input type="email" name="email" required><label>Mật khẩu</label><input type="password" name="password" required><p><small>Mật khẩu ít nhất 12 ký tự.</small></p><button style="width:100%">Tiếp tục</button></form><p style="text-align:center;margin-top:16px">{% if reg %}Đã có tài khoản? <a href="/login">Đăng nhập</a>{% else %}Chưa có tài khoản? <a href="/register">Đăng ký</a>{% endif %}</p><p style="text-align:center"><small>Cần hỗ trợ? Zalo 0819 869 828</small></p></div>',reg=reg,error=error)
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
    return page('<h2>Đơn hàng của tôi</h2><p>Đặt Fanpage mới và theo dõi tiến độ từng đơn. Giá hiện tại: <b style="color:#2563eb">{{money(s.price)}} / Page</b>.</p><div class="panel"><h3>Đặt Fanpage mới</h3><form method="post">'+F+'<label>Tên Fanpage</label><input name="page" required maxlength="250" placeholder="Nhập tên Fanpage cần khởi tạo"><label>Số lượng</label><input type="number" min="1" max="100" value="1" name="qty" id="qty" oninput="document.getElementById(\'sum\').textContent=(this.value*{{s.price}}).toLocaleString(\'vi-VN\')+\'đ\'" required><p>Tổng tiền: <b id="sum" style="color:#2563eb">{{money(s.price)}}</b></p><button>Tạo đơn</button></form><p class="note" style="margin-top:16px">Chưa cấu hình tài khoản ngân hàng. Không chuyển tiền tại bản thử nghiệm. Thanh toán được xác nhận thủ công sau đối soát — liên hệ Zalo 0819 869 828.</p></div>{% for o in rows %}<div class="panel"><div style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:center"><b>{{o.id}}</b><span class="badge {% if o.status==\'Hoàn thành\' %}badge-done{% elif o.status==\'Đã hủy\' %}badge-cancel{% elif o.status in [\'Chờ thanh toán\',\'Chờ xác nhận\'] %}badge-wait{% else %}badge-proc{% endif %}">{{o.status}}</span></div><h3 style="margin-top:12px">{{o.page}}</h3><p>{{money(o.qty*o.price)}} · {{o.qty}} Page · <small>{{o.created}}</small></p>{% if o.status==states[0] %}<form method="post" action="/notify/{{o.id}}">'+F+'<button class="btn-ghost">Thông báo đã chuyển khoản (thử nghiệm)</button></form>{% endif %}{% if o.link %}<p>Link bàn giao: <a href="{{o.link}}">{{o.link}}</a></p>{% endif %}</div>{% else %}<div class="panel"><p>Bạn chưa có đơn hàng nào. Đặt đơn đầu tiên ở form phía trên.</p></div>{% endfor %}',rows=rows,s=s)
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
    return page('''<div class="shell"><aside class="panel" style="padding:16px"><h3 style="margin-bottom:12px">PT AGENCY · ADMIN</h3><a href="#overview">Tổng quan</a><a href="#list">Đơn hàng</a><a href="#customers">Khách hàng</a><a href="#settings">Giá &amp; chi phí</a><a href="#logs">Nhật ký</a><p style="margin-top:16px"><small>Liên hệ: Zalo 0819 869 828</small></p></aside><div><h2 id="overview">Bảng điều hành PT Agency</h2><p>Theo dõi đơn hàng, doanh thu và tiến độ bàn giao Tick Xanh Fanpage.</p><div class="grid">{% for k,v in metrics %}<div class="panel"><small>{{k}}</small><div class="metric">{{v}}</div></div>{% endfor %}</div><div class="panel" id="list"><h3>Quản lý đơn hàng</h3><p>Xác nhận thanh toán chỉ sau khi đối chiếu ngân hàng. Bản thử nghiệm không tự xác nhận giao dịch.</p><div class="scroll"><table><tr><th>Đơn / Khách hàng</th><th>Fanpage / Tiền</th><th>Trạng thái &amp; bàn giao</th></tr>{% for o in rows %}<tr><td><b>{{o.id}}</b><br>{{o.name}}<br><small>{{o.email}}</small></td><td>{{o.page}}<br><b>{{money(o.price*o.qty)}}</b></td><td><form method="post">'''+F+'''<input type="hidden" name="action" value="update"><input type="hidden" name="oid" value="{{o.id}}"><select name="status">{% for st in states %}<option {% if st==o.status %}selected{% endif %}>{{st}}</option>{% endfor %}</select><input name="link" placeholder="Link bàn giao" value="{{o.link}}"><button>Lưu</button></form>{% if o.finished %}<small>Bảo hành 12 tháng từ {{o.finished}}</small>{% endif %}</td></tr>{% endfor %}</table></div></div><div class="panel" id="customers"><h3>Khách hàng ({{customers|length}})</h3>{% for c in customers %}<p>{{c.name}} · {{c.email}}</p>{% else %}<p>Chưa có khách hàng nào đăng ký.</p>{% endfor %}</div><div class="panel" id="settings"><h3>Giá bán &amp; chi phí / Page</h3><form method="post">'''+F+'''<input type="hidden" name="action" value="settings"><div class="grid">{% for k,label in [('price','Giá bán'),('cost','Giá vốn'),('commission','Hoa hồng dự kiến')] %}<div><label>{{label}}</label><input name="{{k}}" type="number" min="0" value="{{s[k]}}" required></div>{% endfor %}</div><button>Lưu cấu hình</button></form><p>Giá vốn và hoa hồng mặc định 0, cần nhập thực tế. Chỉ áp dụng đơn mới.</p></div><div class="panel" id="logs"><h3>Nhật ký quản trị</h3>{% for l in logs %}<p>{{l.created}} · {{l.actor}} · {{l.action}}</p>{% else %}<p>Chưa có nhật ký.</p>{% endfor %}</div></div></div>''',rows=rows,customers=customers,s=s,logs=logs,metrics=[('Tổng đơn',len(rows)),('Tiền đã xác nhận',f"{sum(o['qty']*o['price'] for o in paid):,}đ"),('Hoàn thành',len(done)),('Lãi gộp dự kiến',f"{sum(o['qty']*(o['price']-o['cost']-o['commission']) for o in done):,}đ")])
if __name__=='__main__': app.run(host='127.0.0.1',port=8000)
