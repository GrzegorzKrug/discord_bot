import cv2

from bot_modules.images import create_hulk_taco

""""""
name = "Youshisu"
image = cv2.imread("./bot_modules/src_images/Youshisu.png")

new_fun = create_hulk_taco(image)

cv2.imwrite("avatar_fun_debug.png", new_fun)
# cv2.imshow("Yous", new_fun)
# cv2.waitKey(delay=5_000)
# cv2.destroyAllWindows()
