import os
import random
from flask import Flask, jsonify, render_template, redirect, send_file, url_for, request, session
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
from algorithms import bfr
from algorithms import pcy
from algorithms import winnow

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            algorithm TEXT NOT NULL,
            parameters TEXT NOT NULL,
            file_path TEXT NOT NULL,
            result_path TEXT NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return 'Username already exists'
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            return redirect(url_for('home'))
        return 'Invalid credentials'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/history')
@login_required
def history():
    user_id = session['user_id']
    conn = get_db_connection()
    history_records = conn.execute('SELECT * FROM history WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()
    return render_template('history.html', history_records=history_records)

@app.route('/delete_history', methods=['POST'])
@login_required
def delete_history():
    user_id = session['user_id']
    conn = get_db_connection()
    conn.execute('DELETE FROM history WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('history'))

@app.route('/validate_columns', methods=['POST'])
def validate_columns():
    file = request.files['file']
    columns = request.form['columns']
    column_names = columns.split(',')

    # Save the file temporarily
    temp_path = os.path.join('uploads', 'temp.csv')
    file.save(temp_path)

    # Read the CSV file
    df = pd.read_csv(temp_path)

    # Check if the column names exist in the dataset
    valid_columns = df.columns.tolist()
    is_valid = all(col in valid_columns for col in column_names)

    # Remove the temporary file
    os.remove(temp_path)

    return jsonify({'is_valid': is_valid})

@app.route('/run_algorithms', methods=['POST'])
@login_required
def run_algorithms():
    user_id = session['user_id']
    algorithm = request.form.get('algorithm', None)

    if algorithm == 'bfr':
        # Check if data file is uploaded
        if 'bfr-file' not in request.files or request.files['bfr-file'].filename == '':
            return render_template('error.html', message="Data file is required.")

        data_file = request.files['bfr-file']
        data_file_path = os.path.join('uploads', data_file.filename)
        data_file.save(data_file_path)

        # Validate threshold
        threshold_str = request.form.get('bfr-threshold', '').strip()
        if threshold_str == '':
            return render_template('error.html', message="Threshold is required.")
        try:
            threshold = float(threshold_str)
            if threshold < 0:
                raise ValueError
        except ValueError:
            return render_template('error.html', message="Threshold must be a non-negative number.")

        # Validate number of clusters
        clusters_str = request.form.get('clusters', '').strip()
        if clusters_str == '':
            return render_template('error.html', message="Number of clusters is required.")
        try:
            num_clusters = int(clusters_str)
            if num_clusters < 1:
                raise ValueError
        except ValueError:
            return render_template('error.html', message="Number of clusters must be a positive integer.")

        # Validate columns
        columns_str = request.form.get('columns', '').strip()
        if columns_str == '':
            return render_template('error.html', message="Columns field is required.")

        # Split the columns and strip whitespace
        columns = [col.strip() for col in columns_str.split(',')]
        if len(columns) != 2 or any(col == '' for col in columns):
            return render_template('error.html', message="Please provide two column names separated by a comma.")

        # Read the CSV file and strip whitespace from columns
        data = pd.read_csv(data_file_path)
        data.columns = data.columns.str.strip()  # Strip whitespace from DataFrame column names

        # Check if columns exist in the dataset
        if not set(columns).issubset(data.columns):
            return render_template('error.html', message="Column names must exist in the dataset.")

        # Prepare data for the algorithm
        data_array = np.column_stack((data[columns[0]], data[columns[1]]))

        # Run the BFR algorithm
        clusters = bfr.BFR(data_array, num_clusters, threshold)

        # Plot the results
        plt.figure(figsize=(10, 6))
        plt.title('Clusters of customers')
        plt.xlabel(columns[0])
        plt.ylabel(columns[1])
        for i, cluster in enumerate(clusters):
            if cluster.discard_set:
                points = np.array(cluster.discard_set)
                plt.scatter(points[:, 0], points[:, 1], label=f'Cluster {i+1}')
            plt.scatter(cluster.centroid[0], cluster.centroid[1], c='red', s=200, alpha=0.75, marker='x')
        plt.legend()
        plot_path = os.path.join('static', 'bfr_plot.png')
        plt.savefig(plot_path)
        plt.close()
        parameters = f"threshold={threshold}, num_clusters={num_clusters}, columns={columns}"
        save_history(user_id, algorithm, parameters, data_file_path, plot_path)

        return render_template('result.html', plot_url=plot_path)
    
    elif algorithm == 'pcy':
        if 'pcy-file' not in request.files or request.files['pcy-file'].filename == '':
            return render_template('error.html', message="Data file is required.")
        data_file = request.files['pcy-file']
        data_file_path = os.path.join('uploads', data_file.filename)
        data_file.save(data_file_path)
        target_col_name=request.form['column']
        if target_col_name == '':
            return render_template('error.html', message="Columns field is required.")
            
        data = pd.read_csv(data_file_path)
        data = pd.read_csv(data_file_path)
        data.columns = data.columns.str.strip()  # Strip whitespace from DataFrame column names
        if target_col_name not in data.columns:
            return render_template('error.html', message="Column name must exist in the dataset.")
        frequent_itemsets=pcy.PCY(data, target_col_name)
        items=list(frequent_itemsets.keys())
        item_labels = ['\n'.join(item) for item in items]
        counts = list(frequent_itemsets.values())
        assert len(items) == len(counts), "items and counts must have the same length"
        # Generate random colors for the bars
        colors = [random_color() for _ in range(len(items))]
    
    # Create a bar chart
        plt.figure(figsize=(10, 6))
        plt.bar(item_labels, counts, width=0.3, color=colors, align='center', linewidth=1)
        plt.title('Frequent Item sets')
        plt.xlabel(target_col_name, fontsize=10)
        plt.ylabel('Count', fontsize=10)
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        plt.legend()
        plot_path = os.path.join('static', 'pcy_plot.png')
        plt.savefig(plot_path)
        plt.close()
        parameters = f"target_col={target_col_name}"
        save_history(user_id, algorithm, parameters, data_file_path, plot_path)
        
        return render_template('result.html', plot_url=plot_path)
    elif algorithm == 'winnow':
        if 'winnow-feature-file' not in request.files or request.files['winnow-feature-file'].filename == '':
            return render_template('error.html', message="Data file is required.")
        if 'winnow-label-file' not in request.files or request.files['winnow-label-file'].filename == '':
            return render_template('error.html', message="Data file is required.")
        data_x=request.files['winnow-feature-file']
        data_y=request.files['winnow-label-file']
        data_x_path = os.path.join('uploads', data_x.filename)
        data_x.save(data_x_path)
        data_y_path = os.path.join('uploads', data_y.filename)
        data_y.save(data_y_path)
        x_data=pd.read_csv(data_x_path)
        y_data=pd.read_csv(data_y_path)
        count_1_actual,count_0_actual, count_1_predictions, count_0_predictions, accuracy, plot_path=winnow.winnow(x_data, y_data)
        results_df = pd.DataFrame({
            'Metric': ['Count of 1 in Actual Data', 'Count of 0 in Actual Data', 'Count of 1 in Predictions', 'Count of 0 in Predictions', 'Accuracy'],
            'Value': [count_1_actual, count_0_actual, count_1_predictions, count_0_predictions, accuracy]
        })
        results_csv_path = os.path.join('static', 'winnow_results.csv')
        results_df.to_csv(results_csv_path, index=False)

        parameters = "Winnow algorithm parameters"
        save_history(user_id, algorithm, parameters, data_x_path, plot_path)
        
        return render_template('winnow.html', table=results_df.to_html(index=False), csv_url=results_csv_path,plot_url=plot_path)
    else:
        return 'Invalid algorithm'

def save_history(user_id, algorithm, parameters, file_path, result_path):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO history (user_id, algorithm, parameters, file_path, result_path)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, algorithm, parameters, file_path, result_path))
    conn.commit()
    conn.close()
def random_color():
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    color = '#{:02x}{:02x}{:02x}'.format(r, g, b)
    return color
    
if __name__ == '__main__':
    app.run(debug=True)
