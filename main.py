"""import modules"""
import shutil
from fastapi import FastAPI, Depends , UploadFile
from sqlalchemy.orm import Session
import requests
from database import  engine, get_db , Base
from security.jwt_handler import signJWT_access, signJWT_refresh, decodeJWT
from security.jwt_bearer import JWTBearer
import crud
import models
import schema
Base.metadata.create_all(bind=engine)
app = FastAPI(title="employee registration")

@app.get('/get_user_profile',dependencies=[Depends(JWTBearer())])
async def  get_user(user_id:str, user_db:Session=Depends(get_db)):
    """getting profile by id"""
    receive_user = user_db.query(models.user_register).filter(models.user_register.id==user_id).first()
    return receive_user
@app.post('/user_register')
async def user_register(data:schema.Base, user_db:Session=Depends(get_db)):
    """user registration"""
    receive_data = user_db.query(models.user_register).filter(models.user_register.mobile_no==data.mobile_no).first()
    if receive_data:
        return 'phone number already in db'
    receive_data1 = user_db.query(models.user_register).filter(models.user_register.email==data.email).first()
    if receive_data1:
        return ' email already in db'
    user_details = models.user_register(**data.dict())
    user_db.add( user_details)
    user_db.commit()
    receive_data2 = user_db.query(models.user_register.id).filter(models.user_register.mobile_no==data.mobile_no).first()
    return data,receive_data2
@app.put("/update user_register",dependencies=[Depends(JWTBearer())])
async def update(user_id:str,name:str=None,email:str=None,
                 mobile_no:str=None,sex:str=None, 
                 dob:str=None, password:str=None,
                 user_db:Session=Depends(get_db)):
    """updating an existing user"""
    data = user_db.query(models.user_register).filter(models.user_register.id==user_id).first()
    if data:
        data.name      = name
        data.email     = email
        data.mobile_no = mobile_no
        data.sex       = sex
        data.dob       = dob
        data.password  =password
        user_db.add(data)
        user_db.commit()
        user_db.refresh()
@app.delete('/delete_user_register',dependencies=[Depends(JWTBearer())])
async def delete(user_id:str,user_db:Session=Depends(get_db)):
    """deleting existing user"""
    delete_data=user_db.query(models.user_register).filter(models.user_register.id==user_id).first()
    user_db.delete(delete_data)
    user_db.commit()
    return delete_data
@app.post('/employee login')
def employee_login(email:str, password:str,user_db:Session=Depends(get_db)):
    """login a user by email and password"""
    login_data=user_db.query(models.user_register).filter(models.user_register.email==email, models.user_register.password==password).first()
    if login_data:
        access_token=signJWT_access(login_data.mobile_no)
        refresh_token=signJWT_refresh(login_data.mobile_no)
        return {"message":"login succesfull","access_token":access_token,"refresh_token":refresh_token}
    return "invalid username/password"     
@app.get("/get otp")
async def get_otp(mobile:str,user_db:Session=Depends(get_db)):
    """Get OTP """
    login_mobile=user_db.query(models.user_register).filter(models.user_register.mobile_no==mobile).first()
    if login_mobile:
        url = f"https://2factor.in/API/V1/e58bd034-5ff3-11ed-9c12-0200cd936042/SMS/{mobile}/AUTOGEN/OTP1"
        payload={}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload, timeout=10)
        print(response.text)
        return "otp has sent"
@app.get("/verify otp")
async def verify_otp(mobile:str,otp:str,user_db:Session=Depends(get_db)):
    """Verify otp"""
    login_mobile=user_db.query(models.user_register).filter(models.user_register.mobile_no==mobile).first()
    if login_mobile:
        url = f"https://2factor.in/API/V1/e58bd034-5ff3-11ed-9c12-0200cd936042/SMS/VERIFY3/91{mobile}/{otp}"
        payload={}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload, timeout=10)
        print(response.text)
        return "otp has verified"
@app.post("/profile creation", tags=["profile"])
async def profile_creation(first_name:str, last_name:str,city:str,
                           place_of_birth:str,image:UploadFile,
                           user_db:Session = Depends(get_db),
                           token:str=Depends(JWTBearer())):
    """profile creation by adding image"""                       
    decodedata= decodeJWT(token)
    users = crud.get_user_by_phone(user_db,mobile_no=decodedata['mobile_number'])
    if users:
        profile_id = user_db.query(models.profile).filter(models.profile.user_id==users.id).first()
        if profile_id:
            return "profile already exist"
        file_path = f"profile_img/{image.filename}"
        with open(file_path,"wb") as buffer:
            shutil.copyfileobj(image.file,buffer)
            profile_details=models.profile(first_name= first_name,
                                        last_name = last_name,
                                        city = city,
                                        place_of_birth= place_of_birth,
                                        image = file_path,
                                        user_id=users.id)
        user_db.add(profile_details)
        user_db.commit()                            
        return "profile added succesfully"                          
@app.get('/get_user',dependencies=[Depends(JWTBearer())], tags=["profile"])
async def get_user_profile(user_db:Session = Depends(get_db),
                           token:str=Depends(JWTBearer())):
    """getting a profile from user_profile_table"""
    decodedata= decodeJWT(token)
    users = crud.get_user_by_phone(user_db,mobile_no=decodedata['mobile_number'])
    user_info = user_db.query(models.profile).filter(models.profile.user_id==users.id).first()
    return user_info
@app.delete('/delete_user',dependencies=[Depends(JWTBearer())], tags=["profile"])
async def delete_user_profile(user_db:Session = Depends(get_db),
                              token:str=Depends(JWTBearer())):
    """deleting from user_profile_table"""
    decodedata= decodeJWT(token)
    users = crud.get_user_by_phone(user_db,mobile_no=decodedata['mobile_number'])
    delete_data=user_db.query(models.profile).filter(models.profile.user_id==users.id).first()
    user_db.delete(delete_data)
    user_db.commit()
    return delete_data  
@app.put('/update_user',dependencies=[Depends(JWTBearer())], tags=["profile"])
async def update_user_profile(first_name:str,last_name:str,
                              city:str,place_of_birth:str,
                              user_db:Session = Depends(get_db),
                              token:str=Depends(JWTBearer())):
    """updating a user in user_profile_table"""                          
    decodedata= decodeJWT(token)
    users = crud.get_user_by_phone(user_db,mobile_no=decodedata['mobile_number'])
    update_data = user_db.query(models.profile).filter(models.profile.user_id==users.id).first()
    if  update_data:
        update_data.first_name   = first_name
        update_data.last_name    =last_name
        update_data.city         =city
        update_data.place_of_birth =place_of_birth
        user_db.add(update_data)
        user_db.commit()
        user_db.refresh(update_data)
    return "profile updated"
@app.put("/change password",dependencies=[Depends(JWTBearer())], tags=["profile"])
async def change_password(old_password:str, password1:str, 
                         password2:str,user_db:Session = Depends(get_db),
                         token:str=Depends(JWTBearer())):
    """change password"""                     
    decodedata= decodeJWT(token)
    users = crud.get_user_by_phone(user_db,mobile_no=decodedata['mobile_number'])
    if users.password == old_password :
        if password1 == password2 :
            users.password = password1
            user_db.add(users)
            user_db.commit()
            user_db.refresh(users)
            return "password updated succesfully"
        return "password not matching"
    return "invalid password"        
@app.get("/forgot password", tags=["profile"])
async def forgot_password(mobile:str, user_db:Session=Depends(get_db)):
    """forgot password"""
    login_mobile=user_db.query(models.user_register).filter(models.user_register.mobile_no==mobile).first()
    if login_mobile:
        url = f"https://2factor.in/API/V1/e58bd034-5ff3-11ed-9c12-0200cd936042/SMS/{mobile}/AUTOGEN/OTP1"
        payload={}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload , timeout=10)
        print(response.text)
        return "otp has sent"
    return "not a registered mobile number"    
@app.put("/verify otp", tags=["profile"])
async def confirm_otp(mobile:str, otp:str,new_password:str, confirm_password:str, user_db:Session=Depends(get_db)):
    """verify otp to update password"""
    login_mobile=user_db.query(models.user_register).filter(models.user_register.mobile_no==mobile).first()
    if login_mobile:
        url = f"https://2factor.in/API/V1/e58bd034-5ff3-11ed-9c12-0200cd936042/SMS/VERIFY3/91{mobile}/{otp}"
        payload={}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload, timeout=10)
        print(response.text)
        if new_password==confirm_password:
            login_mobile.password = new_password
            user_db.add(login_mobile)
            user_db.commit()
            user_db.refresh(login_mobile)
            return "password has updated"
        return "password not matching"
    return "invalid otp"
