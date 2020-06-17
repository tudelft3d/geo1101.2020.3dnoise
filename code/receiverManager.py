import fiona

from receiverPoint import ReceiverPoint

class ReceiverManager:

    def __init__(self):
        self.receiver_points = {}

    def read_receiver_points(self, file_path):
        with fiona.open(file_path) as shape: #Open the receiver points shapefile
            for elem in shape:
                geometry = elem["geometry"]
                rec_pt_coords = geometry["coordinates"]
                rec_pt = ReceiverPoint(rec_pt_coords)
                self.receiver_points[rec_pt_coords] = rec_pt

    def determine_source_points(self, source_lines):
        #Go through all the receiver points and get their possible source points
        for rec_pt_coords in self.receiver_points.keys():
            if(rec_pt_coords[0] > 93503 and rec_pt_coords[1] > 441868 and rec_pt_coords[0] < 93516 and rec_pt_coords[1] < 441946):
            #print(rec_pt_coords)
                rec_pt = self.receiver_points[rec_pt_coords]
                rec_pt.find_intersection_points(source_lines)