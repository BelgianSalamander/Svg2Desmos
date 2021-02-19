import xml.etree.ElementTree as ET
import sympy
from math import cos, sin, radians, sqrt, acos, pi, atan2
import pyperclip

DISABLE_SHADING = False
ONLY_SHADING = False
function_count = 0
Y_SIGN = 1

DEFAULT_STROKE = 'none'
DEFAULT_FILL = '#000000'

colors = {
    'white' : '#ffffff',
    'silver' : '#c0c0c0',
    'grey' : '#808080',
    'gray' : '#808080',
    'black' : '#000000',
    'red' : 'ff0000',
    'maroon' : '#800000',
    'yellow' : '#ffff00',
    'olive' : '#808000',
    'lime' : '#00ff00',
    'green' : '#008000',
    'aqua' : '#00ffff',
    'teal' : '#008080',
    'blue' : '#0000ff',
    'navy' : '#000080',
    'fuchsia' : 'ff00ff',
    'purple' : '#800080',
    '#000' : '#000000'
}

##discord_cols = {
##    'url(#paint0_linear)': '#E59080',
##    'url(#paint1_linear)': '#EDA778',
##    'url(#paint2_linear)': '#DC8974',
##    'url(#paint3_linear)': '#5AC0C7',
##    'url(#paint4_linear)': '#5AC0C7'
#}

#colors.update(discord_cols)
print(colors)

def dist(x,y):
    return sqrt(x**2 + y**2)

def rotate_x(x,y,angle):
    return x * sympy.cos(angle) - y * sympy.sin(angle)

def rotate_y(x,y,angle):
    return x * sympy.sin(angle) + y * sympy.cos(angle)

def negative_zero_clamp(n):
    if -0.1 < n < 0:
        return 0
    else:
        return n
class Svg:
    def __init__(self, root, attrib = None, is_top = True):
        self.root = root
        self.is_top = is_top
        self.objects = []
        for child in root:
            tag = child.tag.replace('{http://www.w3.org/2000/svg}', '')
            if attrib is None:
                new_attrib = root.attrib | child.attrib
            else:
                new_attrib = attrib | child.attrib
            if tag == "g":
                self.objects.append(Svg(child, attrib = new_attrib, is_top = False))
            elif tag == "path":
                self.objects.append(Path(**(root.attrib | child.attrib)))
            elif tag == "circle":
                self.objects.append(Circle(**new_attrib))
    
    def to_desmos(self):
        all_commands = []
        for thing in self.objects:
            all_commands = all_commands + thing.to_desmos()
        if self.is_top:
##            print(all_commands[89])
            pyperclip.copy('\n'.join(all_commands))
            print("Amount of functions:",len(all_commands))
        return all_commands

def get_next_number(d, index):
    original_index = index ##Debugging
    number = list('0123456789.-')
    passed_negative = False
    passed_dot = False
    number_buffer = ""
    try:
        while d[index] not in number:
            index += 1
    except:
        print("Original index:",original_index)
        print("Current index:",index)
        print("Full path:",d)
        print("Part of path which caused error:", d[original_index:])
        raise IndexError

    while d[index] in number:
        if passed_negative and d[index] == '-':
            return float(number_buffer), index
        if passed_dot and d[index] == '.':
            return float(number_buffer), index

        if d[index] == '.':
            passed_dot = True

        passed_negative = True
        number_buffer = number_buffer + d[index]

        index += 1
        if index == len(d):
            return float(number_buffer), index
    return float(number_buffer), index

class Circle:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.cx = float(kwargs['cx'])
        self.cy = -float(kwargs['cy'])
        self.r = float(kwargs['r'])

        self.stroke, self.fill = 'black', 'black'

        if 'stroke' in kwargs:
            self.stroke = kwargs['stroke']

        if 'fill' in kwargs:
            self.fill = kwargs['fill']

        if self.stroke in colors:
            self.stroke = colors[self.stroke]

        if self.fill in colors:
            self.fill = colors[self.fill]

    def to_desmos(self):
        latex_contour = fr"\left(x-{self.cx}\right)^{'{2}'}+\left(y-{self.cy}\right)^{'{2}'}={self.r**2}".replace('\\', '\\\\')
        desmos_expr = ['Calc.setExpression({latex : \'' + latex_contour + '\', color : \'' + self.stroke + '\'})']
        if self.fill != 'transparent' and not DISABLE_SHADING:
            fill_expr = fr"\left(x-{self.cx}\right)^{'{2}'}+\left(y-{self.cy}\right)^{'{2}'}\le{self.r**2}".replace('\\', '\\\\')
            desmos = ['Calc.setExpression({latex : \'' + fill_expr+ '\', color : \'' + self.fill + '\', fillOpacity : 1.0})']
            return desmos + desmos_expr
        return desmos_expr


class Path:
    def __init__(self, **kwargs):
        self.d = kwargs['d']
        self.kwargs = kwargs
        d = kwargs['d']

        self.stroke, self.fill = DEFAULT_STROKE , DEFAULT_FILL

        if 'stroke' in kwargs:
            self.stroke = kwargs['stroke']

        if 'fill' in kwargs:
            self.fill = kwargs['fill']

        if self.stroke in colors:
            self.stroke = colors[self.stroke]

        if self.fill in colors:
            self.fill = colors[self.fill]


        self.parts = []
        ##Parsing path
        parts = []
        number_chars = list('0123456789.-')
        path_part_delimiters = {'M': 2,
                                'm': 2,
                                'L': 2,
                                'l': 2,
                                'H': 1,
                                'h': 1,
                                'V': 1, 
                                'v': 1,
                                'Z': 0,
                                'z': 0,
                                'C': 6,
                                'c': 6,
                                'S': 4,
                                's': 4,
                                'Q': 4,
                                'q': 4,
                                'T': 2,
                                't': 2,
                                'A': 7,
                                'a': 7}
        I = 0
        current_command = 'M'
        while I < len(d):
            try:
                while (d[I] not in number_chars) and (d[I] not in path_part_delimiters):
                    I += 1
            except IndexError:
                break
            if d[I] in path_part_delimiters:
                current_command = d[I]            
                I += 1
            segment = [current_command]
            needed_numbers = path_part_delimiters[current_command]
            for i in range(needed_numbers):
                number, I = get_next_number(d, I)
                segment.append(number)
            parts.append(tuple(segment))

        x,y = 0,0
        start_x, start_y = 0,0
        x_control = 0
        y_control = 0
        for part in parts:
            TYPE = part[0]
            if TYPE == 'M':
                x,y = part[1], part[2]
                start_x, start_y = x, y
                x_control, y_control = x,y
            elif TYPE == 'm':
                x += part[1]
                y += part[2]
                start_x, start_y = x, y
                x_control, y_control = x,y
            elif TYPE == 'L':
                self.parts.append(Line(x, y, part[1], part[2]))
                x, y = part[1], part[2]
                x_control, y_control = x,y
            elif TYPE == 'l':
                self.parts.append(Line(x, y, x+part[1], y+part[2]))
                x += part[1]
                y += part[2]
                x_control, y_control = x,y
            elif TYPE == 'H':
                self.parts.append(Line(x, y, part[1], y))
                x = part[1]
                x_control, y_control = x,y
            elif TYPE == 'h':
                self.parts.append(Line(x, y, x + part[1], y))
                x += part[1]
                x_control, y_control = x,y
            elif TYPE == 'V':
                self.parts.append(Line(x, y, x, part[1]))
                y = part[1]
                x_control, y_control = x,y
            elif TYPE == 'v':
                self.parts.append(Line(x, y, x, y + part[1]))
                y += part[1]
                x_control, y_control = x,y
            elif TYPE.lower() == 'z':
                if x != start_x or y != start_y:
                    self.parts.append(Line(x, y, start_x, start_y))
                    x, y = start_x, start_y
                x_control, y_control = x,y
            elif TYPE == 'C':
                self.parts.append(Cubic(x, y, *part[1:]))
                x, y = part[5], part[6]
                x_control, y_control = part[3], part[4]
                
            elif TYPE == 'c':
                self.parts.append(Cubic(x, y, x + part[1], y + part[2], x + part[3], y + part[4], x + part[5], y + part[6]))
                x_control, y_control = x + part[3], y + part[4]
                x += part[5]
                y += part[6]
            elif TYPE == 'S':
                x1, y1 = 2*x - x_control, 2*y - y_control
                self.parts.append(Cubic(x, y, x1, y1, part[1], part[2], part[3], part[4]))
                x = part[3]
                y = part[4]
                x_control, y_control = part[1], part[2]
            elif TYPE == 's':
                x1, y1 = 2*x - x_control, 2*y - y_control
                self.parts.append(Cubic(x, y, x1, y1, x + part[1], y + part[2], x + part[3], y + part[4]))
                x_control, y_control = x + part[1], y + part[2]
                x += part[3]
                y += part[4]
            elif TYPE == 'Q':
                self.parts.append(Quadratic(x, y, part[1], part[2], part[3], part[4]))
                x, y = part[3], part[4]
                x_control, y_control = part[1], part[2]
            elif TYPE == 'q':
                self.parts.append(Quadratic(x, y, x + part[1], y + part[2], x + part[3], y + part[4]))
                x_control, y_control = x + part[1], y + part[2]
                x += part[3]
                y += part[4]
            elif TYPE == 'T':
                x1, y1 = 2*x - x_control, 2*y - y_control
                self.parts.append(Quadratic(x, y, x1, y1, part[1], part[2]))
                x, y = part[1], part[2]
                x_control, y_control = x1, y1
            elif TYPE == 't':
                x1, y1 = 2*x - x_control, 2*y - y_control
                self.parts.append(Quadratic(x, y, x1, y1, x + part[1], y + part[2]))
                x += part[1]
                y += part[2]
                x_control, y_control = x1, y1
            elif TYPE == 'A':
                self.parts.append(Arc(x, y, part[1], part[2], part[3], part[4], part[5], part[6], part[7]))
                x = part[6]
                y = part[7]
                x_control, y_control = x,y
            elif TYPE == 'a':
                self.parts.append(Arc(x, y, part[1], part[2], part[3], part[4], part[5], x + part[6], y + part[7]))
                x += part[6]
                y += part[7]
                x_control, y_control = x,y
            else:
                print("Invalid Character")

    def to_desmos(self):
        do_stroke = (self.stroke != 'none') and not ONLY_SHADING
        do_fill = (self.fill != 'none') and (self.fill != 'transparent') and not DISABLE_SHADING
        ##Stroke of Path
        if do_stroke:
            latex = [part.to_latex().replace('\\', '\\\\') for part in self.parts]
            desmos = ['Calc.setExpression({latex : \'' + expression + '\', color : \'' + self.stroke + '\'})' for expression in latex]
        
        ##Fill of path
        if do_fill:
            start_x, start_y = self.parts[0].x1, -self.parts[0].y1
            end_x, end_y = self.parts[-1].x2, -self.parts[-1].y2

            latex = []

            for i in range(len(self.parts)):
                latex.append(self.parts[i].to_latex(t_offset = i, split_x_y = True))
            if not (start_x == end_x and start_y == end_y):
                latex.append(Line(end_x,end_y,start_x,start_y).to_latex(t_offset = i+1, split_x_y = True))

            func_x = r"\left\{"
            func_y = r"\left\{"

            i = 0
            for x, y in latex[:-1]:
                func_x += fr'{i}\le t<{i+1}:{x},'
                func_y += fr'{i}\le t<{i+1}:{y},'
                i += 1
            func_x += fr'{latex[-1][0]}'+r'\right\}'
            func_y += fr'{latex[-1][1]}'+r'\right\}'

            func = r'\left(' + func_x + ',' + func_y + r'\right)'
            func = func.replace('\\','\\\\')
            full_func = 'Calc.setExpression({latex : \'' + func + '\', color : \'' + self.fill + '\', fill : true, fillOpacity : 1.0, parametricDomain : { min : \'0\', max : \'' + str(len(latex)-1) + '\'}})'
            if ONLY_SHADING:
                return [full_func]

        if do_stroke and not do_fill:
            return desmos
        if do_stroke and do_fill:
            return [full_func] + desmos
        if (not do_stroke) and do_fill:
            return [full_func]
        return []

##Path Subclasses
class Line:
    def __init__(self, x1, y1, x2, y2):
        self.x1, self.x2, self.y1, self.y2 = x1, x2, - Y_SIGN * y1, - Y_SIGN * y2

    def to_latex(self, t_offset = 0, split_x_y = False):
        x1,y1,x2,y2 = self.x1, self.y1, self.x2, self.y2
        x_delta = x2 - x1
        y_delta = y2 - y1
        if t_offset == 0:
            func_x = fr"{x_delta:.20f}t+{x1:.20f}"
            func_y = fr"{y_delta:.20f}t+{y1:.20f}"
        else:
            func_x = fr"{x_delta:.20f}\left(t-{t_offset:.20f}\right)+{x1:.20f}"
            func_y = fr"{y_delta:.20f}\left(t-{t_offset:.20f}\right)+{y1:.20f}"

        if not split_x_y:
            return r'\left(' + func_x + ',' + func_y + r'\right)'
        else:
            return func_x, func_y

class Quadratic:
    def __init__(self, x1, y1, x2, y2, x3, y3):
        self.x1, self.y1, self.x2, self.y2, self.x3, self.y3 = x1, - Y_SIGN * y1, x2, - Y_SIGN * y2, x3, - Y_SIGN * y3

    def to_latex(self, t_offset = 0, split_x_y = False):
        x1,x2,x3,y1,y2,y3 = self.x1, self.x2, self.x3, self.y1, self.y2, self.y3
        if t_offset != 0:
            func_x = fr"\left(1-\left(t-{t_offset}\right)\right)^{2}{negative(x1)}+2\left(1-\left(t-{t_offset}\right)\right)\left(t-{t_offset}\right){negative(x2)}+\left(\left(t-{t_offset}\right)\right)^{2}{negative(x3)}"
            func_y = fr"\left(1-\left(t-{t_offset}\right)\right)^{2}{negative(y1)}+2\left(1-\left(t-{t_offset}\right)\right)\left(t-{t_offset}\right){negative(y2)}+\left(\left(t-{t_offset}\right)\right)^{2}{negative(y3)}"   
        else:
            func_x = fr'\left(1-t\right)^{2}{negative(x1)}+2\left(1-t\right)t{negative(x2)}+\left(t\right)^{2}{negative(x3)}'
            func_y = fr'\left(1-t\right)^{2}{negative(y1)}+2\left(1-t\right)t{negative(y2)}+\left(t\right)^{2}{negative(y3)}'
        if not split_x_y:
            return r'\left(' + func_x + ',' + func_y + r'\right)'
        else:
            return func_x, func_y
class Cubic:
    def __init__(self, x1, y1, x2, y2, x3, y3, x4, y4):
        self.x1, self.y1, self.x2, self.y2, self.x3, self.y3, self.x4, self.y4 = x1, - Y_SIGN * y1, x2, - Y_SIGN * y2, x3, - Y_SIGN * y3, x4, - Y_SIGN * y4
    def to_latex(self, t_offset = 0, split_x_y = False):
        if t_offset == 0:
            func_x = fr'\left(1-t\right)^{3}{negative(self.x1)}+3\left(1-t\right)^{2}\left(t\right){negative(self.x2)}+3\left(1-t\right)\left(t\right)^{2}{negative(self.x3)}+\left(t\right)^{3}{negative(self.x4)}'
            func_y = fr'\left(1-t\right)^{3}{negative(self.y1)}+3\left(1-t\right)^{2}\left(t\right){negative(self.y2)}+3\left(1-t\right)\left(t\right)^{2}{negative(self.y3)}+\left(t\right)^{3}{negative(self.y4)}'
        else:
            func_x = fr'\left(1-\left(t-{t_offset}\right)\right)^{3}{negative(self.x1)}+3\left(1-\left(t-{t_offset}\right)\right)^{2}\left(\left(t-{t_offset}\right)\right){negative(self.x2)}+3\left(1-\left(t-{t_offset}\right)\right)\left(\left(t-{t_offset}\right)\right)^{2}{negative(self.x3)}+\left(\left(t-{t_offset}\right)\right)^{3}{negative(self.x4)}'
            func_y = fr'\left(1-\left(t-{t_offset}\right)\right)^{3}{negative(self.y1)}+3\left(1-\left(t-{t_offset}\right)\right)^{2}\left(\left(t-{t_offset}\right)\right){negative(self.y2)}+3\left(1-\left(t-{t_offset}\right)\right)\left(\left(t-{t_offset}\right)\right)^{2}{negative(self.y3)}+\left(\left(t-{t_offset}\right)\right)^{3}{negative(self.y4)}'
        
        if not split_x_y:
            return r'\left(' + func_x + ',' + func_y + r'\right)'
        else:
            return func_x, func_y
        
class Arc:
    def __init__(self, x1, y1, rx, ry, angle, large_arc, sweep, x2, y2):
        if sweep == 1:
            sweep = 0
        else:
            sweep = 1
        self.x1, self.y1, self.rx, self.ry, self.angle, self.large_arc, self.sweep, self.x2, self.y2 = x1, - Y_SIGN * y1, rx, ry, -radians(angle), int(large_arc), int(sweep), x2, - Y_SIGN * y2
    def to_latex(self, t_offset = 0, split_x_y = False):
        x1, x2, y1, y2, rx, ry = self.x1, self.x2, self.y1, self.y2, self.rx, self.ry

        x_prime = (x1-x2)/2 * cos(self.angle) + (y1-y2)/2 * sin(self.angle)
        y_prime = (y1-y2)/2 * cos(self.angle) - (x1-x2)/2 * sin(self.angle)

        sign = -1 if self.large_arc == self.sweep else 1
        try:
            C = sign * sqrt( negative_zero_clamp( (rx**2 * ry**2 - rx**2 * y_prime**2 - ry**2*x_prime**2) / (rx**2 * y_prime**2 + ry**2 * x_prime ** 2)))
        except:
            return ""
        cx_prime = C * rx * y_prime / ry
        cy_prime = -C * ry * x_prime / rx

        cx = cx_prime * cos(self.angle) - cy_prime * sin(self.angle) + (x1 + x2)/2
        cy = cx_prime * sin(self.angle) + cy_prime * cos(self.angle) + (y1 + y2)/2

        theta_1 = atan2( rotate_y(x1 - cx, y1 - cy, -self.angle) / ry, rotate_x(x1 - cx, y1 - cy, -self.angle) / rx)
        theta_2 = atan2( rotate_y(x2 - cx, y2 - cy, -self.angle) / ry, rotate_x(x2 - cx, y2 - cy, -self.angle) / rx)
        theta_delta = (theta_2 - theta_1) % (2 * pi)

        if not self.sweep:
            theta_delta -= 2*pi
        
        angle = self.angle
        if t_offset == 0:
            func_x = fr"{rx}\cos\left({theta_delta}t+{theta_1}\right)\cdot{cos(angle)}-" +\
            fr"{ry}\sin\left({theta_delta}t+{theta_1}\right)\cdot{sin(angle)}+{cx}"

            func_y = fr"{rx}\cos\left({theta_delta}t+{theta_1}\right)\cdot{sin(angle)}+" +\
            fr"{ry}\sin\left({theta_delta}t+{theta_1}\right)\cdot{cos(angle)}+{cy}"
        else:
            func_x = fr"{rx}\cos\left({theta_delta}\left(t-{t_offset}\right)+{theta_1}\right)\cdot{cos(angle)}-" +\
            fr"{ry}\sin\left({theta_delta}\left(t-{t_offset}\right)+{theta_1}\right)\cdot{sin(angle)}+{cx}"

            func_y = fr"{rx}\cos\left({theta_delta}\left(t-{t_offset}\right)+{theta_1}\right)\cdot{sin(angle)}+" +\
            fr"{ry}\sin\left({theta_delta}\left(t-{t_offset}\right)+{theta_1}\right)\cdot{cos(angle)}+{cy}"
        
        if not split_x_y:
            return r'\left(' + func_x + ',' + func_y + r'\right)'
        else:
            return func_x, func_y



def negative(n):
    if n < 0:
        return r'\left('+ str(n) + r'\right)'
    else:
        return str(n)

if __name__ == "__main__":
    root = ET.parse("logos/NASA.svg").getroot()
    Desmos = Svg(root)
    Desmos.to_desmos()
