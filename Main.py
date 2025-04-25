from GUI import GUI
import pygame

def main():
    try:
        pygame.init()
        gui = GUI()
        while True:
            try:
                gui.draw_menu()
                gui.handle_menu_events()
            except pygame.error:
                break
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
    finally:
        pygame.quit()

if __name__ == "__main__":
    main()