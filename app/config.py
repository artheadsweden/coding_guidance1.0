class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = 'klJnfnkjbsdfh8387gjgf7(&(/56365237465gsdjvJHGVvfva8))'
    MONGO_URI = 'mongodb://cg_root:KLjsdn/636¤737g jhdsfJHfh9bfkjhsd88&76@mongodb:27017/coding_guidance'
    
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
    
class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = True
    