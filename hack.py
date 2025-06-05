from flask import Flask, render_template
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

def create_pie_chart():
    labels = ['Hostel A', 'Hostel B', 'Hostel C']
    sizes = [25, 40, 35]
    colors = ['#ff9999','#66b3ff','#99ff99']

    plt.figure(figsize=(4, 4))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    pie_data = base64.b64encode(img.read()).decode()
    plt.close()
    return pie_data

def create_bar_chart():
    categories = ['January', 'February', 'March']
    values = [100, 150, 90]

    plt.figure(figsize=(5, 4))
    plt.bar(categories, values, color='skyblue')
    plt.title("Electricity Usage")

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    bar_data = base64.b64encode(img.read()).decode()
    plt.close()
    return bar_data

@app.route('/')
def index():
    pie_chart = create_pie_chart()
    bar_chart = create_bar_chart()
    return render_template('hhh.html', pie_chart=pie_chart, bar_chart=bar_chart)

if __name__ == '__main__':
    app.run(debug=True)
