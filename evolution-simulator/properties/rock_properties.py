
#dict with rock properties; UCS_MPA is the uniaxial compressive strength,
#weathering factor is, how resistant the granite is from 0-1, with higher numbers being more resistant.

ROCK_PROPERTIES = {

    "granite": {
        "ucs_mpa": 175.0,
        "weathering_factor": 0.8

    },
    "basalt": {
        "ucs_mpa": 200.0,
        "weathering_factor": 0.7
    },
    "sandstone": {
        "ucs_mpa": 80.0,
        "weathering_factor": 1.2
    },
    "limestone": {
        "ucs_mpa": 100.0,
        "weathering_factor": 1.3
    },
    "shale": {
        "ucs_mpa": 50.0,
        "weathering_factor": 1.8
    }
}
