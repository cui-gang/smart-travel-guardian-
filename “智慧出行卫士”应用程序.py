import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image
import pygame
import os
import sys
from threading import Thread

# 颜色配置（危险等级1-5）
COLOR_SCHEME = {
    'water': {  # 仅受游泳等级影响
        1: (200, 230, 255),  # 安全
        2: (173, 216, 230),
        3: (135, 206, 250),
        4: (70, 130, 180),
        5: (0, 0, 139)        # 危险
    },
    'other': {  # 受年龄和健康等级影响
        1: {'road': (220, 220, 220), 'public': (220, 245, 200), 'community': (255, 220, 200)},
        2: {'road': (150, 150, 150), 'public': (100, 180, 80), 'community': (255, 150, 80)},
        3: {'road': (80, 80, 80), 'public': (30, 100, 50), 'community': (180, 50, 30)},
        4: {'road': (50, 50, 50), 'public': (15, 50, 25), 'community': (100, 25, 15)},
        5: {'road': (20, 20, 20), 'public': (10, 30, 15), 'community': (50, 10, 5)}
    }
}

class MapGenerator:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("智慧出行卫士1.0")
        self.window.geometry("500x450")
        
        # Pygame显示控制
        self.screen = None
        self.running = False
        
        # 初始化控件
        self.img_path = self.load_last_image_path()  # 加载上次选择的地图文件路径
        if self.img_path:
            self.set_background_color()
        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""
        # 年龄输入
        tk.Label(self.window, text="年龄 (0-120岁)", font=('微软雅黑', 11)).pack(pady=5)
        self.age_slider = tk.Scale(self.window, from_=0, to=120, orient=tk.HORIZONTAL, length=400)
        self.age_slider.set(25)  # 默认值
        self.age_slider.pack()

        # 健康等级
        tk.Label(self.window, text="健康等级 (1-5级)", font=('微软雅黑', 11)).pack(pady=5)
        self.health_slider = tk.Scale(self.window, from_=1, to=5, orient=tk.HORIZONTAL, length=400)
        self.health_slider.set(1)  # 默认值
        self.health_slider.pack()

        # 游泳等级（仅影响水域）
        tk.Label(self.window, text="游泳安全等级 (1-5级)", font=('微软雅黑', 11)).pack(pady=5)
        self.swim_slider = tk.Scale(self.window, from_=1, to=5, orient=tk.HORIZONTAL, length=400)
        self.swim_slider.set(1)  # 默认值
        self.swim_slider.pack()

        # 功能按钮
        tk.Button(self.window, text="1-点击选择地图各城市", command=self.load_image,
                 bg="#4CAF50", fg="white", width=35).pack(pady=10)
        tk.Button(self.window, text="2-调整年龄等，点击生成安全地图", command=self.start_conversion,
                 bg="#2196F3", fg="white", width=35).pack()

    def load_last_image_path(self):
        """加载上次选择的地图文件路径"""
        try:
            if os.path.exists('last_image_path.txt'):
                with open('last_image_path.txt', 'r') as f:
                    path = f.read().strip()
                    if os.path.exists(path):
                        return path
        except Exception as e:
            print(f"加载上次选择的地图文件路径时出错: {str(e)}")
        return ""

    def save_last_image_path(self, path):
        """保存当前选择的地图文件路径"""
        try:
            with open('last_image_path.txt', 'w') as f:
                f.write(path)
        except Exception as e:
            print(f"保存当前选择的地图文件路径时出错: {str(e)}")

    def load_image(self):
        """加载地图文件"""
        path = filedialog.askopenfilename(filetypes=[("PNG图片", "*.png")])
        if path:
            try:
                with Image.open(path) as img:
                    bg_color = img.getpixel((0,0))
                    self.window.configure(bg=f'#{bg_color[0]:02x}{bg_color[1]:02x}{bg_color[2]:02x}')
                self.img_path = path
                self.save_last_image_path(path)  # 保存当前选择的地图文件路径
            except Exception as e:
                messagebox.showerror("错误", f"图片加载失败: {str(e)}")

    def calculate_danger_level(self):
        """计算其他区域危险等级（仅年龄+健康）"""
        age = int(self.age_slider.get())
        health = self.health_slider.get()
        
        # 年龄等级计算
        if 18 <= age <= 40:
            age_level = 1
        elif (13 <= age <= 17) or (41 <= age <= 59):
            age_level = 2
        elif (7 <= age <= 12) or (60 <= age <= 75):
            age_level = 3 
        elif (4 <= age <= 6) or (76 <= age <= 120):
            age_level = 4
        else:
            age_level = 5
        
        return max(age_level, health)  # 关键修正：不包含游泳等级

    def start_conversion(self):
        """启动转换线程"""
        if not self.img_path:
            messagebox.showerror("错误", "请先选择地图文件")
            return
        
        # 启动处理线程
        Thread(target=self.process_image, daemon=True).start()

    def process_image(self):
        """核心处理逻辑"""
        try:
            # 获取独立参数
            other_level = self.calculate_danger_level()  # 年龄+健康
            water_level = self.swim_slider.get()          # 仅游泳等级

            # 处理图像
            img = Image.open(self.img_path)
            pixels = img.load()

            for x in range(img.width):
                for y in range(img.height):
                    r, g, b, *a = img.getpixel((x, y))

                    # 水域处理（仅游泳等级）
                    if (r, g, b) == (155, 226, 250):
                        new_color = COLOR_SCHEME['water'][water_level]
                    # 其他区域处理（仅年龄+健康）
                    elif (r, g, b) == (255, 216, 107):  # 道路
                        new_color = COLOR_SCHEME['other'][other_level]['road']
                    elif (r, g, b) == (195, 241, 215):  # 公共设施
                        new_color = COLOR_SCHEME['other'][other_level]['public']
                    elif (r, g, b) == (240, 243, 250):  # 社区
                        new_color = COLOR_SCHEME['other'][other_level]['community']
                    else:
                        continue  # 保留其他颜色

                    pixels[x, y] = new_color + tuple(a) if a else new_color

            # 显示结果
            temp_path = "temp_map.png"
            img.save(temp_path)
            self.show_result(temp_path)
            os.remove(temp_path)

        except Exception as e:
            messagebox.showerror("处理错误", str(e))

    def show_result(self, path):
        """显示结果窗口"""
        if not self.screen:
            self.screen = pygame.display.set_mode((1066, 524))
        img = pygame.image.load(path)
        img = pygame.transform.scale(img, (1066, 524))
        
        self.screen.blit(img, (0,0))
        pygame.display.flip()

        # 非阻塞事件循环
        self.running = True
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.display.quit()

    def set_background_color(self):
        """设置图形化界面背景为使用者所选择的地图文件的颜色"""
        try:
            with Image.open(self.img_path) as img:
                bg_color = img.getpixel((0,0))
                self.window.configure(bg=f'#{bg_color[0]:02x}{bg_color[1]:02x}{bg_color[2]:02x}')
        except Exception as e:
            print(f"设置背景颜色时出错: {str(e)}")

if __name__ == "__main__":
    app = MapGenerator()
    app.window.mainloop()
    pygame.quit()
