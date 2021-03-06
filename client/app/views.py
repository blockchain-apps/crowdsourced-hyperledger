import json
from flask import render_template, request, redirect, url_for, session
from rest.api import *
from client.app import *

pubKey = 'pubkey'
consumerID = "c2"
consumerAccountID = "ca2"
clientTokens = {}
clientForms = {}


def encrypt(randomMessage):
    return randomMessage[::-1]


@app.route('/test', methods=['GET'])
def serve_test():
    return str(getTimestamp())


@app.route('/', methods=['GET','POST'])
@app.route('/requestForm', methods=['GET','POST'])
def requestForm():
    if request.method == 'GET':
        return render_template('request.html')
    else:
        return render_template('request.html',request_ip=request.form['request_ip'])


@app.route('/sendHash', methods=['GET', 'POST'])
def sendHash():
    if request.method == 'POST':
        request_ip = request.form['request-ip']
        session['request-ip'] = request_ip

        url = "http://" + request_ip + ":" + ORGANIZATION_PORT + "/form"
        data = requests.get(url).json()
        randomMessage = data['randomMessage']
        surveyID = data['surveyID']
        if(surveyID is None or surveyID==''):
            return render_template('display.html', display={'error': 'surveyID is None or surveyID=="". Has the organization generated a form yet?'})
        encryptedRandomMessage = encrypt(randomMessage)

        return render_template('sendHash.html',
                               randomMessage=randomMessage,
                               surveyID=surveyID,
                               encryptedRandomMessage=encryptedRandomMessage)
    else:
        return render_template('sendHash.html',
                               randomMessage="Error",
                               encryptedRandomMessage="Error")


@app.route('/generateForm', methods=['GET', 'POST'])
def generateForm():
    if request.method == 'POST':
        if 'from-token' in request.form and request.form['from-token']:
            surveyID = request.form['surveyID']
            surveyToken = request.form['surveyToken']
            form = clientForms[surveyToken]
            return render_template('form.html',
                                   randomMessage='Authenticated',
                                   response=form,
                                   surveyID=surveyID,
                                   surveyToken=surveyToken,
                                   authenticated=True)
        else:
            url = "http://" + session['request-ip'] + ":" + ORGANIZATION_PORT + "/form"
            form = requests.post(url, json={'encryptedRandomMessage': request.form['encryptedRandomMessage'],
                                            'pubKey': pubKey, 'consumerID': consumerID}).json()

            if "error" not in dict(form).keys():
                clientTokens[form['surveyID']] = form['surveyToken']
                clientForms[form['surveyToken']] = form

                print(clientTokens)
                return render_template('form.html',
                                       randomMessage='Authenticated',
                                       response=form,
                                       surveyID=form['surveyID'],
                                       surveyToken=form['surveyToken'],
                                       authenticated=True)
            else:
                return render_template('form.html',
                                       randomMessage=form['error'],
                                       authenticated=False)
    else:
        return redirect(url_for('requestForm'))


@app.route('/publishBlock/<string:surveyID>', methods=['GET', 'POST'])
def publishBlockOnFabric(surveyID):
    if request.method == 'POST':
        filledForm = json.dumps(request.form)
        # TODO: Replace "valid" with filledForm
        postSubmitSurvey(filledForm, clientTokens[surveyID], consumerAccountID)
        return redirect(url_for('requestForm'))


@app.route('/tokens', methods=['GET', 'POST'])
def viewAllTokens():
    if request.method == 'GET':
        clientTokensData = {}
        tokenClaimStatus = {}
        for token in clientTokens:
            assignSurveyToken = getAssignSurveyToken(clientTokens[token])
            tokenClaimStatus[clientTokens[token]] = assignSurveyToken['claimed']
            print(tokenClaimStatus)
            clientTokensData[token] = {'surveyToken': clientTokens[token],
                                       'on-chain': assignSurveyToken}
        return render_template('tokens.html',
                               clientTokens=clientTokensData, claimed=tokenClaimStatus)


@app.route('/display/status')
def serve_display_status():
    display = []
    display.append(getConsumer("c2"))
    display.append(getConsumerAccount("ca2"))
    return render_template('display_blocks.html', display=display)


@app.route('/surveys')
def serve_surveys():
    display = getGeneral('Survey')
    return render_template('surveys.html', display=display)
