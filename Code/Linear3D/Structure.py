import numpy as np
from Element import *
from Node import *
from CrossSection import *
from numpy.linalg import inv
from log_ import *



class Structure:


    def __init__(self, js):
        # Load the jason file and construct the virtual structure
        # Create Node objects and put them in nparray "nodes"

        logger.info("Creating the Virtual Structure for 3D Linear solving\n")

        # self.n_totalFreeDof = 0 #added by pubudu to extractDOF from deformation increment vector
        self.fix_Point_array = []

        self.n_nodes = js["no_of_nodes"]
        self.nodes = np.empty(self.n_nodes, dtype=Node)
        js_nodes = js["nodes"]
        for node in js_nodes:
            id = node["id"]
            p_x = node["x"]
            p_y = node["y"]
            p_z = node["z"]
            logger.debug("Node id= %d, Coordinates [%d %d %d]" % (id, p_x, p_y, p_z))
            new_node = Node(id, p_x, p_y, p_z)
            self.nodes.put(id, new_node)

        # logger.info("Node reading --> Done")
        logger.info("Node reading --> Done")

        # Create CrossSection objects and put them in nparray "cross_sections"
        self.no_of_crosssection_types = js["no_of_crosssection_types"]
        self.cross_sections = np.empty(self.no_of_crosssection_types, dtype=CrossSection)
        js_cross_sections = js["cross_sections"]
        for cross_section in js_cross_sections:
            id = cross_section["id"]
            shape = cross_section["shape"]
            dimensions = cross_section["dimensions"]
            new_cross_section = None
            if shape == "rectangle":
                width = dimensions["y"]
                height = dimensions["z"]
                new_cross_section = SquareCrossSection(id, width, height)



            elif shape == "circle":
                radius = dimensions["radius"]
                new_cross_section = CircularCrossSection(id, radius)

            self.cross_sections.put(id, new_cross_section)

        logger.info("Cross section reading--> Done")

        # Create Element objects and put them in nparray "elements"
        self.n_elements = js["no_of_elements"]
        self.elements = np.empty(self.n_elements, dtype=Element)
        js_elements = js["elements"]
        for element in js_elements:
            id = element["id"]
            start_node_id = element["start_node_id"]
            start_node = self.nodes[start_node_id]
            end_node_id = element["end_node_id"]
            end_node = self.nodes[end_node_id]
            cross_section = self.cross_sections[element["element_type"]]


            yDiff = abs(self.nodes[start_node_id].p_y - self.nodes[end_node_id].p_y)
            xDiff = abs(self.nodes[start_node_id].p_x - self.nodes[end_node_id].p_x)
            zDiff = abs(self.nodes[start_node_id].p_z - self.nodes[end_node_id].p_z)
            length = math.sqrt(math.pow(yDiff, 2) + math.pow(xDiff, 2) + math.pow(zDiff,2))

            theta_x_e=None
            theta_y_e=None
            theta_z_e=None

            new_element = Element(id, start_node, end_node, cross_section, theta_x_e,theta_y_e,theta_z_e, length)
            self.elements.put(id, new_element)
        logger.info("Elements Creation --> Done")

        # Take loads applied and assign them to Nodes
        self.no_of_loads = js["no_of_loads"]
        js_loads = js["loads"]
        for load in js_loads:
            # id = load["id"]
            node_id = load["point_id"]
            force = load["force"]
            f_x = force["x"]
            f_y = force["y"]
            f_z = force["z"]
            torque = load["torque"]
            m_x = torque["x"]
            m_y = torque["y"]
            m_z = torque["z"]

            node = self.nodes[node_id]
            [node.f_x, node.f_y, node.f_z, node.m_x, node.m_y, node.m_z] = [f_x, f_y, f_z, m_x, m_y, m_z]
        logger.info("Loads Assigning--> Done")
        # Take fixed points and assign nodes as fixed
        self.no_of_fixed_points = js["no_of_fixed_points"]
        js_fixed_points = js["fixed_points"]
        for fixed_point in js_fixed_points:
            # id = fixed_point["id"]
            node_id = fixed_point["point_id"]
            translation = fixed_point["translation"]
            self.fix_Point_array += [node_id]
            t_x = translation["x"]
            t_y = translation["y"]
            t_z = translation["z"]

            rotation = fixed_point["rotation"]
            r_x = rotation["x"]
            r_y = rotation["y"]
            r_z = rotation["z"]

            node = self.nodes[node_id]
            [node.t_x, node.t_y, node.t_z, node.r_x, node.r_y, node.r_z] = [t_x, t_y, t_z, r_x, r_y, r_z]


        logger.info("Fixed points Creation--> Done")

        return None
