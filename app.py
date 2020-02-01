
# importing the necessary dependencies
from flask import Flask, render_template, request,jsonify
from flask_cors import CORS,cross_origin
import pickle
import pandas as pd

app = Flask(__name__) # initializing a flask app

@app.route('/',methods=['GET'])  # route to display the home page
@cross_origin()
def homePage():
    return render_template("index.html")

@app.route('/predict',methods=['POST','GET']) # route to show the predictions in a web UI
@cross_origin()
def index():
    if request.method == 'POST':
        try:
            #  reading the inputs given by the user
            fixed_acidity=float(request.form['fixed_acidity'])
            volatile_acidity = float(request.form['volatile_acidity'])
            citric_acid = float(request.form['citric_acid'])
            residual_sugar = float(request.form['residual_sugar'])
            chlorides = float(request.form['chlorides'])
            free_sulfur_dioxide = float(request.form['free_sulfur_dioxide'])
            total_sulfur_dioxide = float(request.form['total_sulfur_dioxide'])
            density = float(request.form['density'])
            pH = float(request.form['pH'])
            sulphates = float(request.form['sulphates'])
            alcohol = float(request.form['alcohol'])




            with open("standardScalar.sav", 'rb') as f:
                scalar = pickle.load(f)

            with open("modelForPrediction.sav", 'rb') as f:
                model = pickle.load(f)

            with open("pca_model.sav", 'rb') as f:
                pca_model = pickle.load(f)

            #prediction=loaded_model.predict([[gre_score,toefl_score]])
            data_df = pd.DataFrame([[fixed_acidity, volatile_acidity, citric_acid, residual_sugar,
                                     chlorides, free_sulfur_dioxide,
                                     total_sulfur_dioxide, density,pH,sulphates,alcohol]])

            scaled_data = scalar.transform(data_df)
            pca_data = pca_model.transform(scaled_data)

            predict = model.predict(pca_data)

            if predict[0] == 3:
                result = 'Bad'
            elif predict[0] == 4:
                result = 'Below Average'
            elif predict[0] == 5:
                result = 'Average'
            elif predict[0] == 6:
                result = 'Good'
            elif predict[0] == 7:
                result = 'Very Good'
            else:
                result = 'Excellent'




            print('prediction is', result)
            # showing the prediction results in a UI



            return render_template('results.html',prediction=result)


        except Exception as e:
            print('The Exception message is: ',e)
            return 'something is wrong'
    # return render_template('results.html')
    else:
        return render_template('index.html')



if __name__ == "__main__":
    #app.run(host='127.0.0.1', port=8001, debug=True)
	app.run(debug=True) # running the app