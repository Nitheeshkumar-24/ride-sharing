from flask import Flask, render_template,request

app = Flask(__name__)

@app.route('/')
def authentication():
    return render_template('authentication.html')

@app.route('/register', method=['POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        full_name = request.form['full-name']

if __name__ == '__main__':
    app.run(debug=True)