from flask import Flask, render_template, request
from flask import redirect, url_for
import json
from modules import codesys_parser as cdp
app = Flask(__name__, static_folder='static', template_folder='static')

@app.route('/')
def home():
    return redirect(url_for('upload'))

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/upload_s2')
def upload2():
    return render_template('upload_s2.html')

@app.route('/upload_s3')
def upload3():
    return render_template('upload_s3.html')

@app.route('/graph')
def graph():
    return render_template('graph.html')

#Codesys submit form URL, limit to post requests
@app.route('/upload-codesys', methods=['POST', 'GET'])
def upload_codesys():
    # Get the form data
    codesys_code = request.form.get('codesys_code')
    # Process the CODESYS code as needed
    parser = cdp.CodesysParser(raw_content=codesys_code)
    parser.read()
    if parser.check_if_codesys_code_is_valid():
        parsed_data, devices = parser.parse_file_content()


        # Return HTML with parsed data and devices {{% mockAddresses %}} {{% devices %}} for upload_s2.html
        # Two variables are passed to the template both need to be JS code
        # Return as Markup, because the template expects JS code. Make sure the characters are not escaped so they don't turn to {&#34;id&#34;: &#34;...&#34;} instead of {"id": "..."}
        return render_template('upload_s2.html', mockAddresses=parsed_data, devices=devices)
    else:
        return "CODESYS code is not valid."

@app.route('/upload-23', methods=['POST'])
def upload_23():
    devices = request.form.get('devices')
    addresses = request.form.get('addresses')

    # Parsed form has single backslash escaped characters, so we need to convert it to a proper JSON object
    devices = json.loads(devices)
    addresses = json.loads(addresses)

    return render_template('upload_s3.html', userProvidedDevices=devices, userProvidedAddresses=addresses)

if __name__ == '__main__':
    app.run(debug=True)