"""
Resumen:
El módulo está pensado para ser utilizado en cualquier web.
Es una clase donde se puede crear una instancia para cada programa ya que puede manipular diversas pestañas si así se requiera.
Su configuración y uso estará definido mediante un diccionario desde donde obtendremos los pasos que el handler tiene que hacer y las configuraciones necesarias para obtener cada elemento.
En otras palabras, el programa sólo lee un diccionario de datos y la configuración del mismo es quién se encarga de ejecutarlo todo.

Proceso:
Cuando se inicia el Handler se le indica por parámetro la configuración general.
Luego se fijan los elementos recurrentes. Cuando tenemos que realizar una acción hay que indicar qué tipo de elemento es, por tanto, cada uno requiere de una config mínima pero se repite contantemente. Por ello podemos dejar guardado los elementos que sabemos que se puede usar más de una vez, pero no es obligatorio.

Al crear el objeto que va a manejar el programa vamos a necesitar una serie de configuraciones y los pasos a seguir, los diccionarios son:
-----------------------------------------------------------------------------------------------------------------------------------------
config:
select_driver: [] / Edge / Chrome / Firefox / Safari > Si está en None, se intentará buscar en la misma carpeta donde estamos el driver y en ese mismo orden. De lo contrario, esperamos una lista de 2 elementos siendo el 1ro un str (ej: "Edge") y el 2do un path para buscarlo.
maximize_window: T/F > Maximizar o no la ventana. Por defecto no ocupa toda la pantalla.
move_mouse: T/F > Indicamos si estamos en presencia de una web que necesita manipular el mouse, en éste caso habría que dar una advertencia.

elements:
- text: True / False > En muchos casos los elementos se deben seleccionar primero para luego hacer clic, en vez de realizarlo en 2 pasos lo configuramos en éste apartado.
- action: clic / edit / select > El select es por si sólo debemos seleccionarlo pero no realizar un clic.
- absolute_path: (str) > 
- relative_path: (str) >

elements:
- text: (str) > 
- type: (str) > Indica el tipo de elemento con el cuál luego vamos a buscarlo con Selenium (NAME, ID, XPATH, etc)
- value: (str) > Valor con el que vamos a buscar el elemento en función a su type.
    - parts: (optional | list) > Cuando tenemos un XPATH por ejemplo que queremos recorrer modificando el valor de una parte del mismo, podemos construirlo dinámicamente. Se espera una lista de 3 partes donde la del medio es un valor que será reemplazado por un número determinado a continuación.
    - 

ejemplo_de_elementos = {
    1: {
        "text": False,
        "type": "NAME",
        "value": "email",
    },
    2: {
        "text": False,
        "type": "XPATH",
        "value": '//*[@id="platform-container"]/div/div/div/div[1]/platform-courses/div/div/div/div/div[2]/div[2]/div[1]/ul/li[1]/a/span',
    },
    # Courses - List.div - Encontrar UN elemento dentro de una lista (Entregas)
    3: {
        "text": "", # Si buscamos algún texto en el elemento para distinguirlo de la lista
        "type": "XPATH",
        "parts": [
            '//*[@id="platform-container"]/div/div/div/div[1]/platform-course/div/div/div[2]/div/div/div/div/div[2]/div[1]/div[3]/div/div[',
            '_pos_',
            ']/a/div/div/div[1]/div/b',
        ],
        # Se recorre el XPATH modificando el valor del campo '_pos_', el mismo se coordina en estas keys (start y end)
        "start": 1,
        "end": 20,
        "end_loop": True,
    },
}


Modo de uso:
-----------
Haciendo uso de sus métodos (run_steps y run_tasks), podemos correr pasos o tareas.
TASKS: Son acciones mínimas encadenadas como pueden ser seleccionar un EDIT y escribir algo. Pueden ser cortas o extensas y se ejecutan en orden.
STEPS: Si necesitamos algo más complejo podemos llamar a los pasos o steps, que se encargan de ejecutar muchas tareas en un bucle pudiendo repetirse las mismas en base a una condición o resultado determinado.

steps:
El método run_steps 

tasks:
{
    "open_url":{
        "url": "www.google.com",
        "new_window": False,
        "change_tab": False,
        },
    "input_text":{
        "
    }

#########################################################################################################################################
ACA PONEMOS LO QUE SABEMOS QUE FALTA INCORPORAR, PERO PRIMERO VAMOS A ENFOCARNOS EN QUE FUNCIONE:
AGREGAR:
(01) - En el init, habría que crear una excepción para cuando no se pudo obtener el driver.
(02)
(03) - Cuando sepa como abrir una web en otra pestaña, es decir, sin cerrar la pestaña actual.
(04) - Ahora sabemos que todo lo que buscamos lo encontramos, pero tenemos que poner un try porque si cambia la web eso pincha, hay que prevenirlo
(XX) - Cambiar todos los prints y explotar al máximo la librería de logging.
(XX) - Para el parámetro de "parts" se construye en base a un lista se crea con valores enteros no pudiendo usar otra opción. Debería ser una lista de valores entonces si fuesen enteros se los puede crear con un range desde la app que lo ejecuta en vez de forzar a ser números desde acá.
(XX) - Cambiar nombre de variable implicity_wait porque ya no hace referencia a lo mismo.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from time import sleep
from datetime import datetime as dt
import threading

import pyautogui as pa


class HandlerWebSelenium:

    def __init__(self, config: dict, elements: list):
        """
        Args:
            config: Recibimos un dict con la info que necesitamos para todo el proceso.
            elements: Forma de identificar y seleccionar cualquier elemento en la web.
        """

        # (01)
        if config["select_driver"]:
            path = config["select_driver"][1]
            if config["select_driver"][0] == "Edge":
                self.driver = webdriver.Edge(path)
            elif config["select_driver"][0] == "Chrome":
                self.driver = webdriver.Chrome(path)
            elif config["select_driver"][0] == "Firefox":
                self.driver = webdriver.Firefox(path)
            elif config["select_driver"][0] == "Safari":
                self.driver = webdriver.Safari(path)
        else:
            # (02) Programar una forma de intentar buscar todos los posibles drivers en la carpeta raíz.
            pass

        if config["maximize_window"]:
                self.driver.maximize_window()
        self.move_mouse = config["move_mouse"]
        self.elements = elements
        self.activity_mouse = False
        self.q_tab = -1

    def run_steps(self, value_return, steps: dict, tasks: dict):
        """
        Método que se encarga de ir leyendo las tareas que se tienen que realizar.
        Las mismas deben tener un metodo que indique cuándo cortar el bucle si se genera uno infinito.
        """
        start = dt.now()
        self.steps = steps
        self.tasks = tasks
        step_counter = 0
        self.list_of_list = []
        name_step = self.steps[step_counter].get('name_step', "NN")
        print(f"\n**** INICIO STEP: {name_step} ****")
        
        while True:
            if not self.steps.get(step_counter, 0):
                break

            if self.steps[step_counter].get("stop", False):
                break
            value = self.run_tasks(self.tasks[self.steps[step_counter]["name_task"]])

            if self.steps[step_counter]["is_false_finish"]:
                if value == False:
                    break

            if self.steps[step_counter]["is_true_continue"]:
                if value:
                    pass
                else:
                    value -= 1
            step_counter += 1
        
        print(f"**** END STEP - time:{dt.now() - start} ****\n")
        
        # Retornamos la lista que se haya generado
        if value_return == "list":
            print(f"Lista a devolver: {self.list_of_list}")
            return self.list_of_list
        return []

    def run_tasks(self, task, element = ""):
        """
        Le llegan tareas, cada una se ejecuta en orden en función a su nombre.
        """
        
        #print(f"Name general task: {task.get('name_task', 'NN')}")
        
        try:
            _lenght = len(task)
            counter = 0
            
            while counter < _lenght:
                for keys, values in task[counter].items():

                    if keys == "exist":
                        continue

                    if keys == "name_task":
                        print("****************************************")
                        print(f"Name task: {task[counter]['name_task']}")
                        continue

                    if keys == "open_url":
                        self.q_tab += 1
                        if values["new_tab"]:
                            self.driver.execute_script("window.open('');")
                            sleep(0.5)
                            self.driver.switch_to.window(self.driver.window_handles[self.q_tab])
                            sleep(0.5)
                        if self.move_mouse:
                            if values["move_mouse"]:
                                threading.Thread(target=self._move_mouse).start()
                        self.driver.get(values["url"])
                        self.driver.implicitly_wait(values.get("implicitly_wait", 10))
                    
                    elif keys == "find_element":
                        element = self._find_element(
                            pos_element=values.get("pos_element", 0),
                            bucle=values.get("implicitly_wait", 50),
                            exist=values.get("exist", False),
                            )

                    elif keys == "find_elements_for_text":
                        _element = self.elements[values["pos_element"]]
                        for pos in range(_element["start"], _element["end"]):
                            try:
                                path = ""
                                for text in _element["parts"]:
                                    if text == "_pos_":
                                        path += str(pos)
                                    else:
                                        path += text

                                new_dict = {
                                    "type": _element["type"],
                                    "value": path,
                                }
                                element = self._find_element(
                            new_dict=new_dict,
                            bucle=values.get("implicitly_wait", 50),
                            exist=values.get("exist", False),
                            )
                                
                                if element.text == _element["search_text"]:
                                    if values["click"]:
                                        element.click()
                                        break
                            except Exception:
                                if values["end_loop"]:
                                    break

                    elif keys == "write":
                        element.send_keys(values["set_text"])

                    elif keys == "click":
                        if values:
                            element = self._find_element(
                                values["pos_element"],
                                bucle=values.get("implicitly_wait", 50),
                                exist=values.get("exist", False)
                                )
                        element.click()
                        print(f"Click in: {values.get('name_element', 'NN')}")

                    elif keys == "loop_list":
                        for pos in range(values["start"], values["end"] + 1):
                            try:
                                path = ""
                                for text in values["parts"]:
                                    if text == "_pos_":
                                        path += str(pos)
                                    else:
                                        path += text

                                new_dict = {
                                    "type": values["type"],
                                    "value": path,
                                }
                                element = self._find_element(False,new_dict)
                                if values["get_text"]:
                                    self.list_of_list.append(element.text)
                                else:
                                    self.list_of_list.append(element)
                            except Exception as e:
                                print(f"ERROR: {type(e).__name__}")
                                if values["end_loop"]:
                                    break
                        print(f"\nContent of the obtained list:\n{self.list_of_list}\n")

                    if values.get("sleep", 0):
                        self.time_sleep(values['sleep'], values.get('type_sleep', "simple_show"))
                counter += 1

        except Exception as e:
            print(f"An error has occurred: {e}")
            return False
        return True

    def _find_element(self, pos_element = 0, new_element = {}, bucle = 0, exist = False):
        # (04)
        if new_element:
            _type = new_element["type"]
            _value = new_element["value"]
            _name_element = new_element.get("name_element", "NN")
        else:
            _type = self.elements[pos_element]["type"]
            _value = self.elements[pos_element]["value"]
            _name_element = self.elements[pos_element].get("name_element", "NN")
        print(f">> Search: {_name_element} > Bucle: {bucle} > Exist: {exist}")

        if _type == "NAME":
            By_VALUE = By.NAME
        elif _type == "CLASS_NAME":
            By_VALUE = By.CLASS_NAME
        elif _type == "CSS_SELECTOR":
            By_VALUE = By.CSS_SELECTOR
        elif _type == "ID":
            By_VALUE = By.ID
        elif _type == "XPATH":
            By_VALUE = By.XPATH
        elif _type == "LINK_TEXT":
            By_VALUE = By.LINK_TEXT
        elif _type == "PARTIAL_LINK_TEXT":
            By_VALUE = By.PARTIAL_LINK_TEXT
            
        while True:
            try:
                element = self.driver.find_element(by=By_VALUE, value=_value)
                if element:
                    print("Found element")
                    return element
            except NoSuchElementException:
                print("Not found element")
                if exist == True and bucle <= 0:
                    print(">> ERROR > NO LOOP - End element search without success")
                    raise NoSuchElementException
                elif not bucle:
                    print(">> ERROR > NO LOOP - End element search without success")
                    return None
                elif bucle == -1:
                    pass
                elif bucle > 0:
                    print("Active search")
                    bucle -= 1
                else:
                    print("End element search without success")
                    return None
            sleep(1)

    def _move_mouse(self):
        """La función se ejecuta mientras la variable move_mouse sea True, por lo que se puede desactivar desde fuera.
        Pero genera 8 bucles recorriendo varias partes de la pantalla y una vez realizado termina sóla.
        Cada bucle contiene 20 iteracciones."""
        
        self.activity_mouse = True
        # Posición inferior izquierda
        eje_x = 0
        eje_y = 0

        # Bucle 1: Horizontal Central
        x = eje_x + 50
        y = eje_x + 540
        counter = 0

        while counter < 20 and self.activity_mouse:
            pa.moveTo(x=x, y=y)
            sleep(0.1)
            x += 100
            counter += 1
        
        # Bucle 2: Horizontal Superior
        x = eje_x + 50
        y = eje_y + 50
        counter = 0
        while counter < 20 and self.activity_mouse:
            pa.moveTo(x=x, y=y)
            sleep(0.1)
            x += 720
            counter += 1
        
        # Bucle 3: Horizontal Inferior
        x = eje_x + 50
        y = eje_y + 360
        counter = 0
        while counter < 20 and self.activity_mouse:
            pa.moveTo(x=x, y=y)
            sleep(0.1)
            x += 100
            counter += 1
        
        # Bucle 4: Diagonal (sup - inf)
        x = eje_x + 50
        y = eje_y + 1050
        counter = 0
        while counter < 20 and self.activity_mouse:
            pa.moveTo(x=x, y=y)
            sleep(0.1)
            x += 100
            y -= 50
            counter += 1
        
        # Bucle 5: Vertical Central
        x = eje_x + 960
        y = eje_y + 1050
        counter = 0
        while counter < 20 and self.activity_mouse:
            pa.moveTo(x=x, y=y)
            sleep(0.1)
            y -= 50
            counter += 1
        
        # Bucle 6: Diagonal (inf - sup)
        x = eje_x + 50
        y = eje_y + 50
        counter = 0
        while counter < 20 and self.activity_mouse:
            pa.moveTo(x=x, y=y)
            sleep(0.1)
            x += 100
            y += 50
            counter += 1
        
        # Bucle 7: Vertical Izquierdo
        x = eje_x + 480
        y = eje_y + 1050
        counter = 0
        while counter < 20 and self.activity_mouse:
            pa.moveTo(x=x, y=y)
            sleep(0.1)
            y -= 50
            counter += 1
        
        # Bucle 8: Vertical Derecho
        x = eje_x + 1440
        y = eje_y + 1050
        counter = 0
        while counter < 20 and self.activity_mouse:
            pa.moveTo(x=x, y=y)
            sleep(0.1)
            y -= 50
            counter += 1
        
        self.move_mouse = False

    def time_sleep(self, time, type_sleep):
        if type_sleep == "simple_show":
            print(f"Sleep: {time}")
            sleep(time)
        elif type_sleep == "seconds_show":
            while time > 0:
                if time > 1:
                    print(f"Sleep: {time}")
                    sleep(1)
                else:
                    print(f"Sleep: {round(time,1)}")
                    sleep(time)
                time -= 1
            print(f"Sleep: 0")
        else:
            sleep(time)

