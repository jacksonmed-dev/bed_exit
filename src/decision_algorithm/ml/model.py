from keras.preprocessing.image import load_img
from keras.preprocessing.image import img_to_array
from Mask_RCNN.mrcnn.config import Config
from Mask_RCNN.mrcnn.model import MaskRCNN


from os.path import isfile, join, realpath, dirname
import configparser

dir_path = dirname(realpath(__file__))
file = join(dir_path, '../../configuration/config.ini')
config = configparser.ConfigParser()
config.read(file)

config_model = config['MODEL']
config_paths = config['PATHS']

# draw an image with detected objects

# define the test configuration
class TestConfig(Config):
     NAME = config_model['NAME']
     GPU_COUNT = int(config_model['GPU_COUNT'])
     IMAGES_PER_GPU = int(config_model['IMAGES_PER_GPU'])
     NUM_CLASSES = int(config_model['NUM_CLASSES'])
# define the model
class Model():
     def load_model(self,image_dir,model_dir):
          model = MaskRCNN(mode='inference', model_dir='./', config=TestConfig())
          # load coco model weights
          model.load_weights(model_dir, by_name=True)
          class_names = ast.literal_eval(config_model['CLASS_NAMES'])
          # visualize the results
          # load photograph
          img = load_img(image_dir)
          img = img_to_array(img)
          # make prediction
          results = model.detect([img], verbose=0)
          # get dictionary for first prediction
          r = results[0]

          dic1 = {"head":[],"shoulder":[],"buttocks":[],"leg":[],"arm":[],"heel":[]}
          for item1, item2 in zip(r['rois'], r['class_ids']):
               name = ""
               if item2 == 1:
                    name = "head"
               elif item2 == 2:
                    name = "shoulder"
               elif item2 == 3:
                    name = "buttocks"
               elif item2 == 4:
                    name = "leg"
               elif item2 == 5:
                    name = "arm"
               elif item2 == 6:
                    name = "heel"
               x1 = [int(item1[0]/6),int(item1[1]/6)]
               x2 = [int(item1[0]/6),int(item1[3]/6)]
               y1 = [int(item1[2]/6),int(item1[1]/6)]
               y2 = [int(item1[2]/6), int(item1[3]/6)]
               list =[x1,x2,y1,y2]
               dic1[name].append(list)

          print(dic1)
          return dic1
#Model().load_model('/home/justin/PycharmProjects/raspberry_pi_bed/src/decision_algorithm/ml/test_img/237.png','/home/justin/PycharmProjects/raspberry_pi_bed/src/decision_algorithm/ml/training/model_file/mask_rcnn_body parts_0050.h5')
