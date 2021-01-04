import os,datetime
import csv,io

from flask import Flask, request, jsonify
from flask import render_template
from flask import make_response
from flask_pymongo import PyMongo

application = Flask(__name__,
                    static_folder='static')

application.config["MONGO_URI"] = 'mongodb://' + \
        os.environ['MONGODB_USER'] + ':'   + \
        os.environ['MONGODB_PASSWORD'] + '@'   + \
        os.environ['MONGODB_HOSTNAME'] + ':27017/' + \
        os.environ['MONGODB_DATABASE']

mongo = PyMongo(application)
db = mongo.db

campaign = db.campaigns.find_one({'label':'Sep20'})
if campaign is None:
    campaign_limit_date = "1970.01.01"
    campaign = "No Campaign found"
else:
    campaign_limit_date = campaign['limit_date'].strftime('%Y.%m.%d')
print(f'Using campaign {campaign}')
print(f'               {campaign_limit_date}')

@application.route('/')
def index():
    return render_template('index.html')



@application.route('/api/summary')
def summary():
    rses   = sorted(x['rse'] for x in db.ukrse.find({},{'rse':1,'_id':0}))
    owners = sorted(db.replicas.distinct('owner'))

    counts = {}
    for rse in rses:
        counts[rse] = db.replicas.count_documents({'rse':rse})

    #db.replicas.groupby({'owner'})

    return jsonify( 
        status=True,
        rses=rses,
        owners = owners,
        counts=counts,
    )


def download_csv(rows,filename='export.csv'):
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerows(rows)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    output.headers["Content-type"] = "text/csv"
    return output



@application.route('/owners')
def owners():
    global campaign

    owners = sorted(db.replicas.distinct('owner'))
    counts = {}
    counts_expired = {}
    for owner in owners:
        counts        [owner] = db.replicas.count_documents({'owner':owner})
        counts_expired[owner] = db.replicas.count_documents({'owner':owner,'created_at':{'$lt':campaign['limit_date']}})

    return render_template('owners.html', owners=owners, counts=counts,expired=counts_expired,limit_date=campaign_limit_date)



@application.route('/owners/<owner>')
def owner_by_rse(owner):
    global campaign
    rses = sorted(x['rse'] for x in db.ukrse.find({},{'rse':1,'_id':0}))
    counts = {}
    counts_expired = {}

    for rse in rses:
        counts        [rse] = db.replicas.count_documents({'owner':owner,'rse':rse})
        counts_expired[rse] = db.replicas.count_documents({'owner':owner,'rse':rse,'created_at':{'$lt':campaign['limit_date']}})
    return render_template('owner_rses.html', owner=owner, rses=rses, counts=counts,expired=counts_expired)




@application.route('/api/owners')
def api_owners():
    owners = sorted(db.replicas.distinct('owner'))
    return jsonify( 
        status=True,
        data=owners,
    )

@application.route('/api/ukrse')
def test():
    data = sorted(x['rse'] for x in db.ukrse.find({},{'rse':1,'_id':0}))

    return jsonify( 
        status=True,
        data=data,
    )


@application.route('/dataset/<dset>')
def dataset_details(dset=None):
    filters={}
    filters['name'] = dset

    data =  db.replicas.find_one(filters,{'_id':0})
    return render_template('dataset_details.html',
        item=data,
    )


@application.route('/replicas')
def replicas():
    query_parameters = request.args
    owner = query_parameters.get('owner')
    scope = query_parameters.get('scope')
    rse   = query_parameters.get('rse')
    name  = query_parameters.get('name')
    older_than = query_parameters.get('older_than')
    csv   = query_parameters.get('csv')

    filters = {}
    if owner:
        filters['owner'] = owner
    if rse:
        filters['rse'] = rse
    if scope:
        filters['scope'] = scope
    if name:
        filters['name'] = name
    if older_than:
        dt_olderthan = datetime.datetime.strptime(older_than,"%Y.%m.%d")
        filters['created_at'] = {'$lt':dt_olderthan}


    data = [x for x in db.replicas.find(filters,{'_id':0}) ]
    if csv:
        to_export = ( (x['rse'],x['scope'],x['name'],';'.join(x['owner']) )  for x in data )
        return download_csv(to_export)


    return render_template('datasets.html',
        data=data,
    )

@application.route('/api/replicas')
def api_replicas():
    query_parameters = request.args
    owner = query_parameters.get('owner')
    scope = query_parameters.get('scope')
    rse   = query_parameters.get('rse')
    name  = query_parameters.get('name')
    older_than = query_parameters.get('older_than')

    filters = {}
    if owner:
        filters['owner'] = owner
    if rse:
        filters['rse'] = rse
    if scope:
        filters['scope'] = scope
    if name:
        filters['name'] = name
    if older_than:
        dt_olderthan = datetime.datetime.strptime(older_than,"%Y.%m.%d")
        filters['created_at'] = {'$lt':dt_olderthan}

    data = [x for x in db.replicas.find(filters,{'_id':0}) ]
    return jsonify( 
        status=True,
        data=data,
    )

if __name__ == "__main__":
    ENVIRONMENT_DEBUG = os.environ.get("APP_DEBUG", True)
    ENVIRONMENT_PORT = os.environ.get("APP_PORT", 5000) 
    application.run(host='0.0.0.0', port=ENVIRONMENT_PORT, debug=ENVIRONMENT_DEBUG)

