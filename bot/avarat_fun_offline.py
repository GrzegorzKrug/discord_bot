import cv2

from bot_modules.images import create_wanted_image, create_hulk_taco, get_avenger_pic

""""""
name = "Youshisu"
youshisu_avatar = cv2.imread("./bot_modules/src_images/Youshisu.png")

avatar_url = r"https://cdn.discordapp.com/avatars/513749299763609630/a_8acab6cd1a769f5b21a42959f4e3f51f.gif?size=128"

output = get_avenger_pic(youshisu_avatar)

cv2.imwrite("avatar_fun_debug.png", output)

# cv2.imshow("Yous", new_fun)
# cv2.waitKey(delay=5_000)
# cv2.destroyAllWindows()
