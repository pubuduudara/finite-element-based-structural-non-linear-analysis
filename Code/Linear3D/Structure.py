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
                width = dimensions["z"]
                height = dimensions["y"]
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
            material_id = element["material_id"]
            local_x_dir = element["local_x_dir"]
            local_y_dir = element["local_y_dir"]
            local_z_dir = element["local_z_dir"]

            local_dirs = [local_x_dir, local_y_dir, local_z_dir]

            new_element = Element(id, start_node, end_node, cross_section, material_id, local_dirs)
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

    def analyzeStructure(self):
        DOF_PER_NODE = 6
        mat_size = DOF_PER_NODE * (self.n_elements + 1)
        structure_k = np.zeros([mat_size, mat_size])
        force_vector = np.zeros(mat_size, dtype=np.float_)
        node_order = [-1] * (DOF_PER_NODE * self.n_nodes)
        for element_id in range(self.n_elements):
            element = self.elements[element_id]
            startNode = element.start_node.id
            endNode = element.end_node.id
            k = element.K_element_global()

            y1 = DOF_PER_NODE * startNode
            y2 = y1 + DOF_PER_NODE
            x1 = DOF_PER_NODE * startNode
            x2 = x1 + DOF_PER_NODE
            structure_k[y1:y2, x1:x2] += k[:DOF_PER_NODE, :DOF_PER_NODE]

            y1 = DOF_PER_NODE * startNode
            y2 = y1 + DOF_PER_NODE
            x1 = DOF_PER_NODE * endNode
            x2 = x1 + DOF_PER_NODE
            structure_k[y1:y2, x1:x2] += k[:DOF_PER_NODE, DOF_PER_NODE:]

            start_node = element.start_node
            force_vector[y1:y2] += start_node.get_dof()
            node_order[y1]=startNode

            y1 = DOF_PER_NODE * endNode
            y2 = y1 + DOF_PER_NODE
            x1 = DOF_PER_NODE * startNode
            x2 = x1 + DOF_PER_NODE
            structure_k[y1:y2, x1:x2] += k[DOF_PER_NODE:, :DOF_PER_NODE]

            y1 = DOF_PER_NODE * endNode
            y2 = y1 + DOF_PER_NODE
            x1 = DOF_PER_NODE * endNode
            x2 = x1 + DOF_PER_NODE
            structure_k[y1:y2, x1:x2] += k[DOF_PER_NODE:, DOF_PER_NODE:]

            end_node = element.end_node
            force_vector[y1:y2] += end_node.get_dof()
            node_order[y1]=endNode

        print("structure_k:", structure_k)
        print("structure_force:", force_vector)


        force_vector_copy = force_vector

        index = 0
        for force in force_vector:
            if math.isnan(force):
                structure_k = np.delete(structure_k, index, 0)
                structure_k = np.delete(structure_k, index, 1)
                force_vector = np.delete(force_vector, index, 0)
            else:
                index += 1

        print("structure_k:", structure_k)
        print("structure_force:", force_vector)

        deformation = np.matmul(np.linalg.inv(structure_k), force_vector)

        print("deformation:", deformation)

        deformation_vector = np.zeros(mat_size, dtype=np.float_)
        index_def = 0
        index_force = 0
        for index_force in range(mat_size):
            if not math.isnan(force_vector_copy[index_force]):
                deformation_vector[index_force] = deformation[index_def]
                index_def += 1
            index_force += 1

        print("deformation_vector", deformation_vector)

        node_order = list(filter(lambda a: a != -1, node_order))
        print("Node order:", node_order)

        for node_id in node_order:
            from_i = node_id*DOF_PER_NODE
            node = self.nodes[node_id]
            node.d_x = deformation_vector[from_i]
            node.d_y = deformation_vector[from_i+1]
            node.d_z = deformation_vector[from_i+2]
            node.dm_x = deformation_vector[from_i+3]
            node.dm_y = deformation_vector[from_i+4]
            node.dm_z = deformation_vector[from_i+5]

        return structure_k
