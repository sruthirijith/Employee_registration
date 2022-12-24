import database
from fastapi import FastAPI, Depends
import models
import schema
from database import SessionLocal, engine
from security.jwt_handler import signJWT_access, signJWT_refresh
from security.jwt_bearer import JWTBearer
import requests



models.Base.metadata.create_all(bind=engine)
db = SessionLocal()

app = FastAPI(title="employee registration")

@app.get('/get_user_profile',dependencies=[Depends(JWTBearer())])
def  get_user(id:str):

     receive_user = db.query(models.user_register).filter(models.user_register.id==id).first()
     return receive_user

@app.post('/user_register')
def user_register(data:schema.Base):
    receive_data = db.query(models.user_register).filter(models.user_register.mobile_no==data.mobile_no).first()
    if receive_data:

        return {'phone number already in db'}
    
    receive_data1 = db.query(models.user_register).filter(models.user_register.email==data.email).first()
    if receive_data1:
        return {' email already in db'}
    try:
        user_details = models.user_register(**data.dict())
        db.add( user_details)
        db.commit()
        receive_data2 = db.query(models.user_register.id).filter(models.user_register.mobile_no==data.mobile_no).first()
         
        
    except:
         return{'db error'}
    return data,receive_data2

@app.put("/update user_register",dependencies=[Depends(JWTBearer())])
def update(id:str,name:str=None,email:str=None,mobile_no:str=None,sex:str=None, dob:str=None, password:str=None):
    data = db.query(models.user_register).filter(models.user_register.id==id).first()
    if not data:
        return 404
        
    data.name      = name
    data.email     = email
    data.mobile_no = mobile_no
    data.sex       = sex
    data.dob       = dob
    data.password  =password

    try:
        db.add(data)
        db.commit()
        db.refresh()
    except:
        pass
    return 200

@app.delete('/delete_user_register',dependencies=[Depends(JWTBearer())])
def delete(id:str):
    delete_data=db.query(models.user_register).filter(models.user_register.id==id).first()
    db.delete(delete_data)
    db.commit()
    return delete_data    

@app.post('/employee login')
def employee_login(email:str, password:str):
    login_data=db.query(models.user_register).filter(models.user_register.email==email, models.user_register.password==password).first()
    if login_data:
        access_token=signJWT_access(login_data.mobile_no)
        refresh_token=signJWT_refresh(login_data.mobile_no)
        
        return{"message":"login succesfull","access_token":access_token,"refresh_token":refresh_token}
    else:
        return("invalid username/password")    

# Get OTP        
@app.get("/get otp")
async def get_otp(mobile:str):
        login_mobile=db.query(models.user_register).filter(models.user_register.mobile_no==mobile)
        if login_mobile:
            url = "https://2factor.in/API/V1/e58bd034-5ff3-11ed-9c12-0200cd936042/SMS/{}/AUTOGEN/OTP1".format(str(mobile))

            payload={}
            headers = {}

            response = requests.request("GET", url, headers=headers, data=payload)

            print(response.text)
            return("otp has sent")


#Verify otp
@app.get("/verify otp")
async def verify_otp(mobile:str,Otp:str):
    login_mobile=db.query(models.user_register).filter(models.user_register.mobile_no==mobile)
    if login_mobile:
        url = "https://2factor.in/API/V1/e58bd034-5ff3-11ed-9c12-0200cd936042/SMS/{}/AUTOGEN/OTP1".format(str(mobile))

        payload={}
        headers = {}

        response = requests.request("GET", url, headers=headers, data=payload)

        print(response.text)
        return("otp has verified")

