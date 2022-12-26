import database
from fastapi import FastAPI, Depends
import models
import schema
from database import SessionLocal, engine, get_db , Base
from security.jwt_handler import signJWT_access, signJWT_refresh, decodeJWT
from security.jwt_bearer import JWTBearer
import requests
import crud
from sqlalchemy.orm import Session

# new dataS

Base.metadata.create_all(bind=engine)
db = SessionLocal()

app = FastAPI(title="employee registration")

#getting profile by id
@app.get('/get_user_profile',dependencies=[Depends(JWTBearer())])
def  get_user(id:str):

     receive_user = db.query(models.user_register).filter(models.user_register.id==id).first()
     return receive_user

#user registration
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

#updating an existing user
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

#deleting existing user
@app.delete('/delete_user_register',dependencies=[Depends(JWTBearer())])
def delete(id:str):
    delete_data=db.query(models.user_register).filter(models.user_register.id==id).first()
    db.delete(delete_data)
    db.commit()
    return delete_data    

#login a user by email and password
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
        login_mobile=db.query(models.user_register).filter(models.user_register.mobile_no==mobile).first()
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
    login_mobile=db.query(models.user_register).filter(models.user_register.mobile_no==mobile).first()
    if login_mobile:
        url = "https://2factor.in/API/V1/e58bd034-5ff3-11ed-9c12-0200cd936042/SMS/VERIFY3/91{}/{}".format(str(mobile),Otp)

        payload={}
        headers = {}

        response = requests.request("GET", url, headers=headers, data=payload)

        print(response.text)
        return("otp has verified")
        
 #profile creation
@app.post("/profile creation", tags=["profile"])
async def profile_creation(data:schema.Profile, db:Session = Depends(get_db),token:str=Depends(JWTBearer())):
    decodedata= decodeJWT(token)
    users = crud.get_user_by_phone(db,mobile_no=decodedata['mobile_number'])
    if users:
        profile_id = db.query(models.profile).filter(models.profile.user_id==users.id).first()
        if profile_id:
            return("profile already exist")
        else:    
            profile_details=models.profile( first_name= data.first_name,
                                        last_name = data.last_name,
                                        city = data.city,
                                        place_of_birth= data.place_of_birth,

                                        user_id =users.id)
            db.add(profile_details)
            db.commit()                            
            return("profile added succesfully")                            
        

#getting a profile from user_profile_table
@app.get('/get_user',dependencies=[Depends(JWTBearer())], tags=["profile"])
async def get_user_profile(db:Session = Depends(get_db),token:str=Depends(JWTBearer())):
    decodedata= decodeJWT(token)
    users = crud.get_user_by_phone(db,mobile_no=decodedata['mobile_number'])
    get_user = db.query(models.profile).filter(models.profile.user_id==users.id).first()
    return get_user


#deleting from user_profile_table    
@app.delete('/delete_user',dependencies=[Depends(JWTBearer())], tags=["profile"])
async def delete_user_profile(db:Session = Depends(get_db),token:str=Depends(JWTBearer())):
    decodedata= decodeJWT(token)
    users = crud.get_user_by_phone(db,mobile_no=decodedata['mobile_number'])
    delete_data=db.query(models.profile).filter(models.profile.user_id==users.id).first()
    db.delete(delete_data)
    db.commit()
    return delete_data  

#updating a user in user_profile_table
@app.put('/update_user',dependencies=[Depends(JWTBearer())], tags=["profile"])
async def update_user_profile(first_name:str,last_name:str,city:str,place_of_birth:str,db:Session = Depends(get_db),token:str=Depends(JWTBearer())):
    decodedata= decodeJWT(token)
    users = crud.get_user_by_phone(db,mobile_no=decodedata['mobile_number'])
    update_data = db.query(models.profile).filter(models.profile.user_id==users.id).first()
    if  update_data:
        
        update_data.first_name   = first_name
        update_data.last_name    =last_name
        update_data.city         =city
        update_data.place_of_birth =place_of_birth

    
    db.add(update_data)
    db.commit()
    db.refresh(update_data)
    
    return ("profile updated")


#change password
@app.put("/change password",dependencies=[Depends(JWTBearer())], tags=["profile"])
async def change_password(old_password:str, password1:str, password2:str,db:Session = Depends(get_db),token:str=Depends(JWTBearer())):
    decodedata= decodeJWT(token)
    users = crud.get_user_by_phone(db,mobile_no=decodedata['mobile_number'])
    
    if users.password == old_password :
        if password1 == password2 :
            users.password = password1
            db.add(users)
            db.commit()
            db.refresh(users)
            return "password updated succesfully"
        else:    
            return "password not matching"

    else:
        return "invalid password"        

            
#forgot password
@app.get("/forgot password", tags=["profile"])
async def forgot_password(mobile:str):
    login_mobile=db.query(models.user_register).filter(models.user_register.mobile_no==mobile).first()
    if login_mobile:
        url = "https://2factor.in/API/V1/e58bd034-5ff3-11ed-9c12-0200cd936042/SMS/{}/AUTOGEN/OTP1".format(str(mobile))

        payload={}
        headers = {}

        response = requests.request("GET", url, headers=headers, data=payload)

        print(response.text)
        return("otp has sent")
    else:
        return "not a registered mobile number"    

          
#verify otp to update password
@app.put("/verify otp", tags=["profile"])
async def verify_otp(mobile:str, otp:str,new_password:str, confirm_password:str):
    login_mobile=db.query(models.user_register).filter(models.user_register.mobile_no==mobile).first()
    if login_mobile:
        url = "https://2factor.in/API/V1/e58bd034-5ff3-11ed-9c12-0200cd936042/SMS/VERIFY3/91{0}/{1}".format(str(mobile),otp)

        payload={}
        headers = {}

        response = requests.request("GET", url, headers=headers, data=payload)

        print(response.text)
        
        if new_password==confirm_password:
            login_mobile.password = new_password
            db.add(login_mobile)
            db.commit()
            db.refresh(login_mobile)
            return("password has updated")
        else:
            return "password not matching"
    else:
        return "invalid otp"            


          




    



    
    
    


       

