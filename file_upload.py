import os
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Specify the folder where uploaded files will be saved
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Handle file upload here
        uploaded_file = request.files['file']
        if uploaded_file.filename != '':
            # Generate a unique filename to avoid overwriting existing files
            filename = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
            
            # Save the file to the specified folder
            uploaded_file.save(filename)
            
            return "File uploaded and saved successfully."
        else:
            return "No file selected."
    else:
        # Render an HTML form that allows file upload when accessed with GET method.
        return render_template_string('''
          <form method="post" enctype="multipart/form-data">
              <input type="file" name="file">
              <input type="submit">
          </form>
          ''')

if __name__ == '__main__':
    app.run(debug=True)