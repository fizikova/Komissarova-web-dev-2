from flask import Flask, request, render_template, make_response, redirect, url_for
import re

app = Flask(__name__)

@app.route('/')
def index():
    msg = request.url
    return render_template('index.html', msg=msg)

@app.route('/args')
def args():
    return render_template('args.html')

@app.route('/headers')
def headers():
    return render_template('headers.html')

@app.route('/cookies')
def cookies():
    resp = make_response(render_template('cookies.html'))
    if 'name' not in request.cookies:
        resp.set_cookie('name', 'Bob')
    else:
        resp.set_cookie('name', expires=0)
    return resp

@app.route('/form', methods=['GET','POST'])
def form():
    return render_template('form.html')

@app.route('/phone_form', methods=['GET', 'POST'])
def phone_form():
    raw = ''
    digits = ''
    status = None  # 'character mismatch', 'length discrepancy' или 'good'
    
    if request.method == 'POST':
        raw = request.form.get('phone', '')
        digits = re.sub(r'\D', '', raw)
        pattern = r'^[0-9()+.\s-]+$'
        if not re.match(pattern, raw):
            status = 'character mismatch'
        elif len(digits) not in (10, 11):
            status = 'length discrepancy'
        elif len(digits) == 11 and not digits.startswith(('7', '8')):
            status = 'length discrepancy'
        else:
            status = 'good'
    
    return render_template(
        'phone_form.html',
        raw=raw,
        digits=digits,
        status=status
    )