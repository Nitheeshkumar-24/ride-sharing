from flask import Flask, render_template,request

app = Flask(__name__)

@app.route('/')
def authentication():
    return render_template('authentication.html')

@app.route('/index')
def index():
    return render_template('index.html')
        

if __name__ == '__main__':
    app.run(debug=True)