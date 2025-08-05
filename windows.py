# MIT License
#
# Copyright (c) 2025 Photon (photon.berne@gmail.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import time
import os
import json
from pynput import keyboard
from pynput.mouse import Controller, Button
import threading
import tkinter as tk
import openai
from tkinter import messagebox
API_KEY = ""
BASE_URL = ""
MODEL = ""
root = None
listener = None
CONFIG_FILE = 'config.json'
DEFAULT_CONFIG = {
    'base_url': '',
    'api_key': '',
    'model': ''
}
input_window = None
text_display_window = None
DEBUG_MODE = True
ai_is_responding = False
SCREEN_WIDTH = 0
SCREEN_HEIGHT = 0
conversation_history = []
MAX_HISTORY_LENGTH = 1000

def debug_print(message):
    if DEBUG_MODE:
        print(f"[DEBUG] {message}")

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'api_key' in config and config['api_key'] != 'your-api-key-here':
                    global API_KEY,BASE_URL,MODEL
                    API_KEY = config['api_key']
                    openai.api_key = API_KEY
                    BASE_URL = config['base_url']
                    openai.base_url = BASE_URL
                    MODEL = config['model']

                return config
        except Exception as e:
            debug_print(str(e))
    return DEFAULT_CONFIG.copy()

def click_bottom_center():
    mouse = Controller()
    target_x = SCREEN_WIDTH // 2
    target_y = SCREEN_HEIGHT - 100
    mouse.position = (target_x, target_y)
    mouse.click(Button.left, 1)

def on_key_press(key):
    global esc_pressed, input_window, text_display_window
    global shift_press_count, shift_timer, double_shift_timeout, last_shift_release_time
    global ctrl_press_count, ctrl_timer, double_ctrl_timeout, last_ctrl_release_time
    global esc_press_count, esc_timer, double_esc_timeout, last_esc_release_time

    if 'shift_press_count' not in globals():
        global shift_press_count, shift_timer, double_shift_timeout, last_shift_release_time
        shift_press_count = 0
        shift_timer = None
        double_shift_timeout = 250
        last_shift_release_time = 0

    if 'ctrl_press_count' not in globals():
        global ctrl_press_count, ctrl_timer, double_ctrl_timeout, last_ctrl_release_time
        ctrl_press_count = 0
        ctrl_timer = None
        double_ctrl_timeout = 250
        last_ctrl_release_time = 0

    if 'esc_press_count' not in globals():
        global esc_press_count, esc_timer, double_esc_timeout, last_esc_release_time
        esc_press_count = 0
        esc_timer = None
        double_esc_timeout = 250
        last_esc_release_time = 0

    if key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
        current_time = time.time() * 1000
        if current_time - last_shift_release_time < double_shift_timeout:
            shift_press_count += 1
        else:
            shift_press_count = 1
        if shift_press_count == 1:
            if shift_timer:
                shift_timer.cancel()
            shift_timer = threading.Timer(double_shift_timeout / 1000.0, reset_shift_count)
            shift_timer.start()
        elif shift_press_count == 2:
            if shift_timer:
                shift_timer.cancel()
            on_double_shift()
            reset_shift_count()

    elif key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:

        current_time = time.time() * 1000
        if current_time - last_ctrl_release_time < double_ctrl_timeout:
            ctrl_press_count += 1
        else:
            ctrl_press_count = 1
        if ctrl_press_count == 1:
            if ctrl_timer:
                ctrl_timer.cancel()
            ctrl_timer = threading.Timer(double_ctrl_timeout / 1000.0, lambda: reset_count('ctrl'))
            ctrl_timer.start()
        elif ctrl_press_count == 2:
            if ctrl_timer:
                ctrl_timer.cancel()
            on_double_ctrl()
            reset_count('ctrl')

    elif key == keyboard.Key.esc:
        current_time = time.time() * 1000
        if current_time - last_esc_release_time < double_esc_timeout:
            esc_press_count += 1
        else:
            esc_press_count = 1
        if esc_press_count == 1:
            if esc_timer:
                esc_timer.cancel()
            esc_timer = threading.Timer(double_esc_timeout / 1000.0, lambda: reset_count('esc'))
            esc_timer.start()
        elif esc_press_count == 2:
            if esc_timer:
                esc_timer.cancel()
            on_double_esc()
            reset_count('esc')
            return

def on_key_release(key):
    global  esc_pressed, last_shift_release_time, last_ctrl_release_time, last_esc_release_time
    if key == keyboard.Key.esc:
        esc_pressed = False
        last_esc_release_time = time.time() * 1000
    elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
        last_shift_release_time = time.time() * 1000
    elif key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
        last_ctrl_release_time = time.time() * 1000

def reset_shift_count():
    global shift_press_count, shift_timer
    shift_press_count = 0
    shift_timer = None

def reset_count(key_type):
    if key_type == 'shift':
        global shift_press_count, shift_timer
        shift_press_count = 0
        shift_timer = None
    elif key_type == 'ctrl':
        global ctrl_press_count, ctrl_timer
        ctrl_press_count = 0
        ctrl_timer = None
    elif key_type == 'esc':
        global esc_press_count, esc_timer
        esc_press_count = 0
        esc_timer = None

def on_double_shift():
    global input_window, text_display_window

    try:
        input_visible = input_window and input_window.window and input_window.window.winfo_viewable()
        text_visible = text_display_window and text_display_window.window and text_display_window.window.winfo_viewable()
        if input_visible or text_visible:
            if input_visible:
                input_window.window.withdraw()

            if text_visible:
                text_display_window.window.withdraw()

        else:
            if input_window and input_window.window:
                input_window.window.deiconify()
                input_window.window.lift()
                input_window.window.focus_force()
                input_window.text_input.focus_set()

            if text_display_window and text_display_window.window:
                text_display_window.window.deiconify()
                text_display_window.window.lift()

    except Exception as e:
        debug_print(str(e))

def on_double_ctrl():
    global input_window, root

    if root:
        if input_window and input_window.window:

            input_window.close()
            input_window = None

        input_window = MatrixInputWindow(root)
        input_window.show()
    else:
        pass

def on_double_esc():
    global root, listener

    try:
        if input_window and input_window.window and input_window.window.winfo_viewable():

            input_window.close()
        else:

            return
        if text_display_window and text_display_window.window and text_display_window.window.winfo_viewable():

            text_display_window.close()
        if listener:

            listener.stop()
        if root:

            root.quit()
            root.destroy()

    except Exception as e:

        import os
        os._exit(0)

def clear_conversation_history():
    global conversation_history
    conversation_history = []


def get_conversation_summary():
    global conversation_history
    user_messages = len([msg for msg in conversation_history if msg['role'] == 'user'])
    ai_messages = len([msg for msg in conversation_history if msg['role'] == 'assistant'])
    return f"User message: {user_messages}, AI Reply: {ai_messages}, Total: {len(conversation_history)}"

def initialize_text_display_if_needed():
        global text_display_window, root
        if not text_display_window or text_display_window.is_destroyed:

            text_display_window = MatrixTextDisplay(root)
            initial_content = [
                ">>> MATRIX AI INTERFACE ACTIVATED <<<",
                f"SESSION START: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                "READY FOR INPUT...",
                ""
            ]
            text_display_window.matrix_texts = initial_content
            text_display_window.show()
            return True
        return False


def start_keyboard_listener():
    listener = keyboard.Listener(
        on_press=on_key_press,
        on_release=on_key_release
    )
    listener.start()
    return listener

class AnimatedWindow:
    def __init__(self, parent, initial_alpha=0.0):
        self.parent = parent
        self.alpha = initial_alpha
        self.target_alpha = 0.85
        self.animation_speed = 0.08
        self.is_animating = False
        self.scale = 0.3
        self.target_scale = 1.0
        self.scale_speed = 0.12
        self.original_geometry = None
        self.animation_id = None
        self.is_cancelled = False

    def animate_in(self):
        if self.is_animating or self.is_cancelled:
            return
        self.is_animating = True
        self.alpha = 0.0
        self.scale = 0.3
        self.original_geometry = self.parent.geometry()
        self._animate()

    def animate_out(self, callback=None):
        if self.is_cancelled:
            if callback:
                callback()
            return
        self.is_animating = True
        self.target_alpha = 0.0
        self.target_scale = 0.3
        self.callback = callback
        self._animate()

    def cancel_animation(self):
        self.is_cancelled = True
        if self.animation_id and self.parent:
            try:
                self.parent.after_cancel(self.animation_id)

            except:
                pass
            finally:
                self.animation_id = None
        self.is_animating = False

    def _animate(self):
        if not self.is_animating or self.is_cancelled or not self.parent:
            return
        try:
            self.parent.winfo_exists()
            self.alpha += (self.target_alpha - self.alpha) * self.animation_speed
            self.scale += (self.target_scale - self.scale) * self.scale_speed
            self.parent.attributes('-alpha', self.alpha)
            self._apply_scale_effect()
            alpha_diff = abs(self.alpha - self.target_alpha)
            scale_diff = abs(self.scale - self.target_scale)
            if alpha_diff > 0.01 or scale_diff > 0.01:
                self.animation_id = self.parent.after(16, self._animate)
            else:
                self.alpha = self.target_alpha
                self.scale = self.target_scale
                self.is_animating = False
                if self.target_alpha == 0.0 and hasattr(self, 'callback') and self.callback:
                    self.callback()
        except tk.TclError:

            self.is_animating = False
        except Exception as e:

            self.is_animating = False
            if hasattr(self, 'callback') and self.callback:
                self.callback()

    def _apply_scale_effect(self):
        try:
            if not self.original_geometry or self.is_cancelled:
                return
            parts = self.original_geometry.split('+')
            if len(parts) >= 3:
                size_part = parts[0]
                original_x = int(parts[1])
                original_y = int(parts[2])
                original_width, original_height = map(int, size_part.split('x'))
                new_width = int(original_width * self.scale)
                new_height = int(original_height * self.scale)
                offset_x = (original_width - new_width) // 2
                offset_y = (original_height - new_height) // 2
                new_x = original_x + offset_x
                new_y = original_y + offset_y
                self.parent.geometry(f"{new_width}x{new_height}+{new_x}+{new_y}")
        except Exception as e:
            debug_print(str(e))

class AnimatedWindowInput:
    def __init__(self, parent, initial_alpha=0.0):
        self.parent = parent
        self.alpha = initial_alpha
        self.target_alpha = 0.85
        self.animation_speed = 0.08
        self.is_animating = False
        self.scale = 0.3
        self.target_scale = 1.0
        self.scale_speed = 0.12
        self.original_geometry = None
        self.on_in_complete = None

    def animate_in(self):
        self.is_animating = True
        self.alpha = 0.0
        self.scale = 0.3
        self.target_alpha = 0.85
        self.target_scale = 1.0
        self.original_geometry = self.parent.geometry()
        self._animate()

    def animate_out(self, callback=None):
        self.is_animating = True
        self.target_alpha = 0.0
        self.target_scale = 0.3
        self.callback = callback
        self._animate()

    def _animate(self):
        if not self.is_animating:
            return
        alpha_diff = abs(self.alpha - self.target_alpha)
        scale_diff = abs(self.scale - self.target_scale)
        if alpha_diff > 0.01 or scale_diff > 0.01:
            self.alpha += (self.target_alpha - self.alpha) * self.animation_speed
            self.scale += (self.target_scale - self.scale) * self.scale_speed
            try:
                self.parent.attributes('-alpha', self.alpha)
                self._apply_scale_effect()
                self.parent.after(16, self._animate)
                if scale_diff <0.1:
                        self.on_in_complete()
            except:
                self.is_animating = False
        else:
            self.alpha = self.target_alpha
            self.scale = self.target_scale
            self.is_animating = False
            try:
                self.parent.attributes('-alpha', self.alpha)
                self._apply_scale_effect()
                if self.target_alpha == 0.0 and hasattr(self, 'callback') and self.callback:
                    self.callback()
                else:
                    if hasattr(self, 'on_in_complete') and self.on_in_complete:
                        pass
            except:
                pass

    def _apply_scale_effect(self):
        try:
            if not self.original_geometry:
                return
            parts = self.original_geometry.split('+')
            if len(parts) >= 3:
                size_part = parts[0]
                original_x = int(parts[1])
                original_y = int(parts[2])
                original_width, original_height = map(int, size_part.split('x'))
                new_width = int(original_width * self.scale)
                new_height = int(original_height * self.scale)
                offset_x = (original_width - new_width) // 2
                offset_y = (original_height - new_height) // 2
                new_x = original_x + offset_x
                new_y = original_y + offset_y
                self.parent.geometry(f"{new_width}x{new_height}+{new_x}+{new_y}")
        except Exception as e:

            pass

class RoundedFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg='#000000')

class MatrixTextDisplay:
    def __init__(self, root):
        self.root = root
        self.window = None
        self.animator = None
        self.text_display = None
        self.typewriter_timer = None
        self.is_closing = False
        self.is_destroyed = False
        self.is_streaming = False
        self.stream_buffer = ""
        self.stream_timer = None
        self.fast_mode = False
        self.in_fast_line = False
        self.matrix_texts = [
            ">>> HELP <<<",
            "*DOUBLE PRESS SHIFT TO TOGGLE VISIBILITY.",
            "*INPUT /NEW FOR NEW CHAT.VISIT github.com/ai-sns FOR MORE HELP",
            "",
            "SYSTEM INITIALIZATION... [OK]",
            "NEURAL NETWORK ACTIVATED... [OK]",
        ]

    def set_streaming_content(self, content_lines):
        self.matrix_texts = content_lines
        self.current_line = 0
        self.current_char = 0
        self.is_streaming = True
        if self.text_display:
            self.text_display.config(state='normal')
            self.text_display.delete('1.0', tk.END)
            self.text_display.config(state='disable')
        self.type_next_char()

    def clear_content(self):
        self.matrix_texts = []
        self.current_line = 0
        self.current_char = 0
        self.is_streaming = True
        if self.text_display:
            self.text_display.config(state='normal')
            self.text_display.delete('1.0', tk.END)
            self.text_display.config(state='disable')

    def append_streaming_line(self, line):

        if not isinstance(self.matrix_texts, list):
            self.matrix_texts = []
        self.matrix_texts.append(line)

    def type_next_char(self):
        if (self.is_closing or self.is_destroyed or
                not self.window or not self.text_display):
            return
        try:

            if self.current_line >= len(self.matrix_texts):
                if not self.is_streaming:

                    return
                else:

                    self.typewriter_timer = self.window.after(10, self.type_next_char)
                    return
            current_text = self.matrix_texts[self.current_line]



            if self.fast_mode:
                if current_text.startswith(">>> USER ["):
                    self.in_fast_line = True

                elif self.in_fast_line:
                    if current_text.strip() == "AI IS THINKING...":
                        self.in_fast_line = False

                    else:
                        pass

            if self.current_char < len(current_text):
                if self.in_fast_line:
                    remaining_text = current_text[self.current_char:]
                    self.text_display.config(state='normal')
                    self.text_display.insert(tk.END, remaining_text)
                    self.text_display.config(state='disable')
                    self.text_display.see(tk.END)
                    self.current_char = len(current_text)

                    self.typewriter_timer = self.window.after(5, self.type_next_char)
                else:
                    self.text_display.config(state='normal')
                    self.text_display.insert(tk.END, current_text[self.current_char])
                    self.text_display.config(state='disable')
                    self.text_display.see(tk.END)
                    self.current_char += 1
                    if ">>>" in current_text or "<<<" in current_text:
                        delay = 5
                    elif current_text.startswith("AI ") or current_text.startswith("USER "):
                        delay = 5
                    else:
                        delay = 5
                    self.typewriter_timer = self.window.after(delay, self.type_next_char)
            else:
                self.text_display.config(state='normal')
                self.text_display.insert(tk.END, '\n')
                self.text_display.config(state='disable')
                self.text_display.see(tk.END)
                self.current_line += 1
                self.current_char = 0

                self.typewriter_timer = self.window.after(10, self.type_next_char)
        except Exception as e:

            import traceback

            self._cleanup_timers()

    def stop_streaming(self):
        pass

    def _cleanup_timers(self):

        if hasattr(self, 'typewriter_timer') and self.typewriter_timer and self.window:
            try:
                self.window.after_cancel(self.typewriter_timer)

            except:
                pass
            finally:
                self.typewriter_timer = None
        if hasattr(self, 'stream_timer') and self.stream_timer and self.window:
            try:
                self.window.after_cancel(self.stream_timer)

            except:
                pass
            finally:
                self.stream_timer = None
    def show(self):

        if self.window or self.is_destroyed:

            return
        try:

            self.window = tk.Toplevel(self.root)
            self.window.title("MATRIX AI CONSOLE")
            self.window.configure(bg='black')

            self.window.overrideredirect(True)
            self.window.attributes('-topmost', True)
            self.window.attributes('-alpha', 0.0)
            self.window.wm_attributes('-toolwindow', True)
            window_width = 800
            window_height = 600
            x = max(0, min(SCREEN_WIDTH - window_width, (SCREEN_WIDTH - window_width) // 2))
            y = max(0, min(SCREEN_HEIGHT - window_height, (SCREEN_HEIGHT - window_height) // 2))-50

            self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            self.window.update_idletasks()
            self.window.update()

            self._create_ui_components()

            self.window.bind('<KeyPress-Escape>', self.on_escape)
            self.window.bind('<Escape>', self.on_escape)
            self.window.protocol("WM_DELETE_WINDOW", self.close)

            self.window.focus_force()
            self.window.update_idletasks()
            self.window.update()

            self.animator = AnimatedWindow(self.window)
            self.animator.original_geometry = self.window.geometry()

            self.animator.animate_in()

            self.start_typewriter_effect()

            self.window.lift()
            self.window.focus_force()
            self.window.update_idletasks()
            self.window.update()
        except Exception as e:

            import traceback

            if self.window:
                try:
                    self.window.destroy()
                except:
                    pass
                self.window = None

    def _create_ui_components(self):
        try:
            main_frame = RoundedFrame(self.window, bg='#001100', bd=0, relief='flat')
            main_frame.pack(fill='both', expand=True, padx=10, pady=10)
            inner_frame = tk.Frame(main_frame, bg='#001100', bd=3, relief='solid')
            inner_frame.pack(fill='both', expand=True, padx=6, pady=6)
            title_label = tk.Label(inner_frame, text=">>> MATRIX AI CONSOLE <<<",
                                   fg='#00FF00', bg='#001100',
                                   font=('Courier New', 16, 'bold'))
            title_label.pack(pady=10)
            self.text_display = tk.Text(inner_frame, height=25, width=80,
                                        bg='#001100', fg='#00FF00',
                                        font=('Courier New', 12),
                                        bd=1, relief='solid',
                                        state='normal',
                                        highlightthickness=1,
                                        highlightcolor='#00FF00')
            self.text_display.pack(pady=10, padx=20, fill='both', expand=True)
            hint_label = tk.Label(inner_frame, text="Press ESC to close",
                                  fg='#00AA00', bg='#001100',
                                  font=('Courier New', 10))
            hint_label.pack(pady=5)

        except Exception as e:

            raise

    def start_typewriter_effect(self):
        if self.is_closing or self.is_destroyed or not self.text_display:

            return

        self.current_line = 0
        self.current_char = 0
        self.type_next_char()

    def on_escape(self, event=None):
        if self.is_closing or self.is_destroyed:
            return 'break'
        try:

            self.close()
        except Exception as e:
            debug_print(str(e))
        return 'break'

    def close(self):
        global text_display_window,input_window
        if input_window:
            input_window.close()
        if self.is_closing or self.is_destroyed:

            return

        self.is_closing = True
        self._cleanup_timers()
        if self.animator:
            try:
                self.animator.cancel_animation()
            except:
                pass
        if self.window and self.animator and not self.is_destroyed:
            try:
                self.animator.animate_out(self._destroy_window)
            except:

                self._destroy_window()
        else:
            self._destroy_window()

    def _destroy_window(self):
        global text_display_window
        if self.is_destroyed:
            return

        self.is_destroyed = True
        self._cleanup_timers()
        if self.animator:
            self.animator = None
        if self.window:
            try:
                self.window.unbind('<KeyPress-Escape>')
                self.window.unbind('<Escape>')
                self.window.destroy()

            except Exception as e:
                debug_print(str(e))
            finally:
                self.window = None
        if text_display_window == self:
            text_display_window = None

            clear_conversation_history()

    def append_content_to_display(self, content_lines):

        if not isinstance(content_lines, list):
            content_lines = [str(content_lines)]
        if not hasattr(self, 'matrix_texts') or not isinstance(self.matrix_texts, list):
            self.matrix_texts = []
        old_length = len(self.matrix_texts)
        self.matrix_texts.extend(content_lines)

        self.is_streaming = True
        if not hasattr(self, 'current_line') or not hasattr(self, 'current_char'):
            self.current_line = 0
            self.current_char = 0

        elif self.current_line >= old_length:
            self.current_line = old_length
            self.current_char = 0

        if hasattr(self, 'typewriter_timer') and self.typewriter_timer:
            try:
                self.window.after_cancel(self.typewriter_timer)
            except:
                pass
            self.typewriter_timer = None

        self.type_next_char()

    def append_content_immediately(self, content_lines):
        if not isinstance(content_lines, list):
            content_lines = [str(content_lines)]
        for line in content_lines:
            if hasattr(self, 'text_widget'):
                self.text_widget.insert(tk.END, line + '\n')
                self.text_widget.see(tk.END)

    def debug_display_state(self):
        if hasattr(self, 'matrix_texts') and self.matrix_texts:
            pass


class MatrixInputWindow:
    def __init__(self, root):
        self.root = root
        self.window = None
        self.animator = None
        self.title_label = None
        self.focus_retry_count = 0
        self.focus_timer = None
        self.initial_focus_set = False
        self.shift_press_count = 0
        self.shift_timer = None
        self.double_shift_timeout = 250

    def show(self):

        if self.window:

            return
        try:
            self.ensure_root_window_ready()
            self.window = tk.Toplevel(self.root)
            self.window.title("")
            self.window.configure(bg='black')
            self.window.overrideredirect(True)
            self.window.attributes('-topmost', True)
            self.window.attributes('-alpha', 0.0)
            self.window.wm_attributes('-topmost', 1)
            self.window.wm_attributes('-toolwindow', True)
            window_width = 798
            window_height = 140
            x = (SCREEN_WIDTH - window_width) // 2
            y = SCREEN_HEIGHT - 40 - window_height
            self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            main_frame = RoundedFrame(self.window, bg='#001100', bd=0, relief='flat')
            main_frame.pack(fill='both', expand=True, padx=8, pady=8)
            inner_frame = tk.Frame(main_frame, bg='#001100', bd=2, relief='solid')
            inner_frame.pack(fill='both', expand=True, padx=4, pady=4)
            self.title_label = tk.Label(inner_frame, text="",
                                        fg='#001100', bg='#001100',
                                        font=('Courier New', 12, 'bold'))
            self.title_label.pack(pady=5)
            self.text_input = tk.Text(inner_frame, height=3, width=70,
                                      bg='#001100', fg='#00FF00',
                                      font=('Courier New', 10),
                                      insertbackground='#00FF00',
                                      bd=1, relief='solid',
                                      highlightthickness=1,
                                      highlightcolor='#00FF00')
            self.text_input.pack(pady=5, padx=10, fill='both', expand=True)
            hint_label = tk.Label(inner_frame, text="ESC to unload | Double Ctrl to load | Double ESC to quit",
                                  fg='#00AA00', bg='#001100',
                                  font=('Courier New', 8))
            hint_label.pack(pady=2)
            self.text_input.bind('<Return>', self.on_enter)
            self.text_input.bind('<Escape>', self.on_escape)
            self.window.bind('<Escape>', self.on_escape)
            self.window.bind('<FocusOut>', self.on_focus_out)
            self.window.after(50, self.delayed_initial_focus_setup)
            self.animator = AnimatedWindowInput(self.window)
            self.animator.on_in_complete = self.start_title_animation
            self.animator.animate_in()
            self.cursor_blink()

        except Exception as e:

            if self.window:
                self.window.destroy()
                self.window = None

    def ensure_root_window_ready(self):
        try:
            if self.root:
                self.root.update_idletasks()
                self.root.update()
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
                self.root.withdraw()
                time.sleep(0.1)

        except Exception as e:
            debug_print(str(e))

    def delayed_initial_focus_setup(self):

        try:
            self.window.lift()
            self.window.attributes('-topmost', True)
            self.window.focus_force()
            self.window.update_idletasks()
            self.window.update()
            self.window.grab_set()
            self.text_input.focus_set()
            self.window.update()
            self.initial_focus_set = True

            self.schedule_focus_check()
            click_bottom_center()
        except Exception as e:
            debug_print(str(e))

    def force_focus_immediate(self):
        if not self.window:
            return
        try:
            if not self.initial_focus_set:
                self.window.lift()
                self.window.attributes('-topmost', True)
                self.window.update_idletasks()
                self.window.after(10, self._complete_initial_focus)
            else:
                self.window.lift()
                self.window.focus_force()
                self.window.grab_set()
                self.text_input.focus_set()
                self.window.update_idletasks()
                self.window.update()
                self.schedule_focus_check()
        except Exception as e:
            debug_print(str(e))

    def _complete_initial_focus(self):
        try:
            self.window.focus_force()
            self.window.grab_set()
            self.text_input.focus_set()
            self.window.update()
            self.initial_focus_set = True
            self.schedule_focus_check()

        except Exception as e:
            debug_print(str(e))

    def schedule_focus_check(self):
        if not self.window:
            return
        if self.focus_timer:
            try:
                self.window.after_cancel(self.focus_timer)
            except:
                pass
        check_interval = 50 if not self.initial_focus_set else 100
        self.focus_timer = self.window.after(check_interval, self.check_and_restore_focus)

    def check_and_restore_focus(self):
        return
        if not self.window:
            return
        try:
            current_focus = self.window.focus_get()
            if current_focus != self.text_input:

                self.window.lift()
                self.window.focus_force()
                self.text_input.focus_set()
                self.window.update()
                self.focus_retry_count += 1

            max_retries = 20 if not self.initial_focus_set else 10
            if self.focus_retry_count < max_retries:
                self.schedule_focus_check()
            else:
                pass
        except Exception as e:
            debug_print(str(e))

    def on_focus_out(self, event):
        return
        if self.window and event.widget == self.window:

            self.window.after(10, self.force_focus_immediate)
            return 'break'

    def start_title_animation(self):
        if not self.window or not self.title_label:
            return
        self.title_label.config(text=">>> MATRIX AI TERMINAL <<<")
        if not self.initial_focus_set:
            self.force_focus_immediate()
        self.current_color = 170
        self.target_color = 255
        self.color_step = 5
        self.animate_title_color()

    def on_enter(self, event):
        global text_display_window, ai_is_responding
        if event.state & 0x1:
            return
        content = self.text_input.get("1.0", tk.END).strip()
        if content:
            if ai_is_responding:

                self.text_input.delete("1.0", tk.END)
                self.text_input.insert("1.0", "AI is still responding, please wait...")
                self.window.after(2000, lambda: self.clear_waiting_message(content))
                return 'break'

            global conversation_history
            conversation_history.append({"role": "user", "content": content})
            if len(conversation_history) > MAX_HISTORY_LENGTH:
                conversation_history = conversation_history[-MAX_HISTORY_LENGTH:]
            user_input_lower = content.lower().strip()
            if user_input_lower in ['/new', '/reset']:
                clear_conversation_history()
                if text_display_window:
                    text_display_window.clear_content()
                    text_display_window.matrix_texts = ["NEW CONVERSATION START... [OK]"]
            else:
                self.show_ai_response(content)
            self.text_input.delete("1.0", tk.END)
            if text_display_window:
                text_display_window.window.deiconify()
            self.window.grab_release()
        return 'break'

    def clear_waiting_message(self,content):
        if self.window and self.text_input:
            current_content = self.text_input.get("1.0", tk.END).strip()
            if current_content == "AI is still responding, please wait...":
                self.text_input.delete("1.0", tk.END)
                self.text_input.insert("1.0", content)

    def show_ai_response(self, user_input):
        global text_display_window, root
        if not text_display_window or text_display_window.is_destroyed:

            text_display_window = MatrixTextDisplay(root)
            text_display_window.show()
            root.after(1000, lambda: self.start_ai_stream(user_input))
        else:

            self.start_ai_stream(user_input)

    def start_ai_stream(self, user_input):
        global ai_is_responding
        if not text_display_window or text_display_window.is_destroyed:

            return
        ai_is_responding = True

        user_input_content = [
            "",
            f">>> USER [{time.strftime('%H:%M:%S')}] <<<",
            f"{user_input}",
            "",
            "AI IS THINKING..."
        ]

        if len(user_input)>120:
            text_display_window.fast_mode = True
        else:
            text_display_window.fast_mode = False
        text_display_window.append_content_to_display(user_input_content)
        def run_openai_stream():
            streamer = OpenAIStreamer()
            def on_stream_content(line):
                if text_display_window and not text_display_window.is_destroyed:

                    root.after(0, lambda l=line: text_display_window.append_content_to_display([l]))
            def on_complete(full_response):
                global ai_is_responding
                ai_is_responding = False


                if text_display_window and not text_display_window.is_destroyed:
                    root.after(0, lambda: text_display_window.stop_streaming())
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    streamer.stream_chat_response(
                        user_input,
                        callback=on_stream_content,
                        complete_callback=on_complete
                    )
                )
                loop.close()
            except Exception as e:
                ai_is_responding = False

                if text_display_window and not text_display_window.is_destroyed:
                    error_lines = [
                        "",
                        f"ERROR: {str(e)}",
                        "Please check the network or api configuration."
                    ]
                    root.after(0, lambda: text_display_window.append_content_to_display(error_lines))
        openai_thread = threading.Thread(target=run_openai_stream, daemon=True)
        openai_thread.start()

    def on_escape(self, event):

        global text_display_window
        if text_display_window:
            text_display_window.close()
        self.close()
        return 'break'

    def close(self):
        global input_window

        if self.focus_timer:
            try:
                self.window.after_cancel(self.focus_timer)
            except:
                pass
        if self.window:
            try:
                self.window.grab_release()
            except:
                pass
        if self.window and self.animator:
            self.animator.animate_out(self._destroy_window)
        else:
            self._destroy_window()

    def _destroy_window(self):
        global input_window

        if self.window:
            try:
                self.window.grab_release()
            except:
                pass
            self.window.destroy()
            self.window = None
            self.animator = None
        if input_window == self:
            input_window = None

    def cursor_blink(self):
        if self.window and self.text_input:
            try:
                current_cursor = self.text_input.cget('insertbackground')
                new_cursor = '#00FF00' if current_cursor == '#001100' else '#001100'
                self.text_input.config(insertbackground=new_cursor)
                self.window.after(500, self.cursor_blink)
            except:
                pass

    def animate_title_color(self):
        if not self.window or not self.title_label:
            return
        self.current_color += self.color_step
        if self.current_color <= self.target_color:
            self.current_color = self.target_color
        else:
            self.window.after(30, self.animate_title_color)
        hex_color = f"#00{self.current_color:02X}00"
        self.title_label.config(fg=hex_color)

    def show_command_result(self, result):
        global text_display_window, root
        if not text_display_window or text_display_window.is_destroyed:
            text_display_window = MatrixTextDisplay(root)
            text_display_window.show()
            root.after(1000, lambda: self._display_command_result(result))
        else:
            self._display_command_result(result)

    def _display_command_result(self, result):
        if text_display_window and not text_display_window.is_destroyed:
            command_content = [
                ">>> MATRIX COMMAND EXECUTED <<<",
                result,
                "--- COMMAND COMPLETE ---"
            ]
            text_display_window.set_streaming_content(command_content)

class OpenAIStreamer:
    def __init__(self, api_key=None,base_url=None,model=None):
        self.api_key = api_key or API_KEY
        self.base_url = base_url or BASE_URL
        self.model = model or MODEL
        openai.api_key = self.api_key
        openai.base_url = self.base_url

    async def stream_chat_response(self, message, callback=None, complete_callback=None):
        global conversation_history, ai_is_responding



        try:
            client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant."}
            ]
            messages.extend(conversation_history)
            if callback:
                ai_header = [
                    "",
                    f">>> AI [{time.strftime('%H:%M:%S')}] <<<"
                ]
                for line in ai_header:
                    callback(line)
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                max_tokens=2048,
                temperature=0.7
            )
            full_response = ""
            current_line = ""
            for chunk in response:
                if not hasattr(chunk, 'choices') or len(chunk.choices) == 0:
                    continue
                choice = chunk.choices[0]
                if not hasattr(choice, 'delta') or not hasattr(choice.delta, 'content'):
                    continue
                if choice.delta.content is None:
                    continue
                content = choice.delta.content
                full_response += content
                current_line += content
                if '\n' in current_line or len(current_line) > 80:
                    lines = current_line.split('\n')
                    for i, line in enumerate(lines[:-1]):
                        if line.strip() and callback:
                            callback(line.strip())
                    current_line = lines[-1]
                elif len(current_line) > 80 and any(punct in current_line for punct in '.!?;,'):
                    if callback:
                        callback(current_line.strip())
                    current_line = ""
            if current_line.strip() and callback:
                callback(current_line.strip())
            if full_response.strip():
                conversation_history.append({"role": "assistant", "content": full_response.strip()})
            if callback:
                completion_lines = [
                    "",
                    "--- RESPONSE COMPLETE ---",
                    f"[Round {len([msg for msg in conversation_history if msg['role'] == 'user'])} | History: {len(conversation_history)} messages]",
                    ""
                ]
                for line in completion_lines:
                    callback(line)
            if complete_callback:
                complete_callback(full_response)

        except Exception as e:
            ai_is_responding = False
            error_msg = f"OpenAI API Error: {str(e)}"

            if callback:
                callback("")
                callback(f"ERROR: {error_msg}")
                callback("")
            if complete_callback:
                complete_callback("")

def main():
    global root, input_window, text_display_window,SCREEN_WIDTH,SCREEN_HEIGHT
    root = None
    input_window = None
    text_display_window = None
    start_keyboard_listener()
    load_config()
    root = tk.Tk()
    SCREEN_WIDTH = root.winfo_screenwidth()
    SCREEN_HEIGHT = root.winfo_screenheight()
    root.title("MATRIX AI")
    root.withdraw()
    root.after(100, show_startup_message)
    root.mainloop()

def show_startup_message():
    print("[INFO] MATRIX AI Started.")
    print("[INFO] Double press Ctrl to show chat terminal.")
    print("[INFO] Double press Esc to quit the application.")
    messagebox.showinfo(
        "Info",
        "Matrix AI Started.\nYou can double click Ctrl key to load terminal.",
        parent=root
    )

if __name__ == "__main__":
    main()
