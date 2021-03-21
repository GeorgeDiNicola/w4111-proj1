
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, url_for
from flask_login import login_required, current_user
import auth
import sql


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = "secret"
app.register_blueprint(auth.bp)

DATABASEURI = "postgresql://gd2581:482543@34.73.36.248/project1" # Modify this with your own credentials you received from Joseph!


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None


@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: https://flask.palletsprojects.com/en/1.1.x/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  # DEBUG: this is debugging code to see what request looks like
  print(request.args)
  return redirect(url_for('auth.login'))


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
@app.route('/home')
@auth.login_required
def home():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data
  """
  lister_info = g.conn.execute(sql.GET_DETAILED_LISTER_INFO)

  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:

  #context = dict(data = names)
  #context = lister_info

  return render_template("index.html", data=lister_info)

  #return render_template("index.html", **context)

@app.route('/lister_detail/<lister_id>')
@auth.login_required
def lister_info(lister_id):
  l_id = str(lister_id)
  sched = g.conn.execute("SELECT au.first_name, au.last_name, s.hour_num, s.date, s.start_time, s.end_time, h.schedule_id, au.city, au.state, au.zip, l.lister_id FROM Application_User au JOIN lister l ON au.user_id = l.user_id JOIN has h ON l.lister_id = h.lister_id JOIN schedule s ON h.schedule_id = s.schedule_id WHERE h.lister_id = %s", l_id)
  reviews = g.conn.execute("SELECT au.first_name, au.last_name, r.comment, r.rating FROM review r INNER JOIN reviews rs on rs.review_id = r.review_id INNER JOIN client c on c.client_id = rs.client_id INNER JOIN application_user au on au.user_id = c.user_id WHERE rs.lister_id = %s", l_id)

  return render_template("lister_detail.html", data=sched, reviews=reviews)


@app.route('/lister_detail/result', methods=('GET', 'POST'))
@auth.login_required
def result():
  schedule_id = request.args.get('s')
  lister_id = request.args.get('l')
  city = request.args.get('c')
  state = request.args.get('st')
  zip_code = request.args.get('z')
  user_id = g.user

  # get client_id of logged in user
  client_id = g.conn.execute(
            "SELECT client_id FROM Client WHERE user_id = %s", (g.user,)
        ).fetchone()

  client_id = client_id[0]

  error = None

  # get count of current clients
  count = g.conn.execute("SELECT COUNT(*) as tot FROM Appointment").fetchone()
  new_appt_id = count['tot'] + 1

  if error is None:
    # create appointment
    g.conn.execute(
      'INSERT INTO Appointment (appointment_id, city, state, zip, schedule_id) VALUES (%s, %s, %s, %s, %s)',
        new_appt_id, city, state, zip_code, schedule_id
    )
    # add Tutors relation
    g.conn.execute(
      'INSERT INTO Tutors (appointment_id, lister_id, client_id) VALUES (%s, %s, %s)',
      new_appt_id, lister_id, client_id
    )
    # update has relation
    g.conn.execute(
      'UPDATE Has SET booked = TRUE WHERE lister_id = %s AND schedule_id = %s',
      lister_id, schedule_id
    )

  return redirect(url_for('appointments'))


@app.route('/appointments')
@auth.login_required
def appointments():

  appointment_info = g.conn.execute(
    '''SELECT c.activity_type, c.activity_name, 
          CONCAT(au2.first_name, ' ', au2.last_name) as lister_full_name, CONCAT(a.city, ', ', a.state, ', ', a.zip) as location,
          s.date, s.start_time, s.end_time
       FROM application_user au
       JOIN client cl ON cl.user_id = au.user_id
       JOIN tutors t ON t.client_id = cl.client_id
       JOIN lister l ON l.lister_id = t.lister_id
       JOIN appointment a ON a.appointment_id = t.appointment_id
       JOIN application_user au2 ON au2.user_id = l.user_id
       JOIN schedule s ON s.schedule_id = a.schedule_id
       JOIN cat_appt cat ON cat.appointment_id = a.appointment_id
       JOIN category c ON c.category_id = cat.category_id
       WHERE au.user_id = %s''', (g.user,)
  )

  count = appointment_info.rowcount

  return render_template("appointments.html", data=appointment_info, count=count) 


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
