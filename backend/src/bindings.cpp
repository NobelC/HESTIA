#include <pybind11/pybind11.h>
#include <pybind11/stl.h> // Para conversiones std::vector <-> list
#include "../include/ResponseProcessor.hpp"

namespace py = pybind11;
using namespace hestia;

PYBIND11_MODULE(hestia_core, m) {
    m.doc() = "HESTIA Core Backend Engine bindings for Python";

    // Módulo BKT
    py::module_ m_bkt = m.def_submodule("bkt", "BKT Module");
    
    py::class_<bkt::SkillState>(m_bkt, "SkillState")
        .def(py::init<>())
        .def_readwrite("pLearn_operative", &bkt::SkillState::m_pLearn_operative)
        .def_readwrite("pLearn_theorical", &bkt::SkillState::m_pLearn_theorical)
        .def_readwrite("pGuess", &bkt::SkillState::m_pGuess)
        .def_readwrite("pSlip", &bkt::SkillState::m_pSlip)
        .def_readwrite("pForget", &bkt::SkillState::m_pForget)
        .def_readwrite("pTransition", &bkt::SkillState::m_pTransition)
        .def_readwrite("avg_response_time_ms", &bkt::SkillState::avg_response_time_ms)
        .def_readwrite("skill_id", &bkt::SkillState::skill_id)
        .def_readwrite("total_attempts", &bkt::SkillState::total_attempts)
        .def_readwrite("session_count", &bkt::SkillState::session_count)
        .def_readwrite("consecutive_correct", &bkt::SkillState::consecutive_correct)
        .def_readwrite("consecutive_error", &bkt::SkillState::consecutive_error)
        .def_readwrite("is_initialized", &bkt::SkillState::is_initialized);

    py::class_<bkt::BKTEngine>(m_bkt, "BKTEngine")
        .def(py::init<>());

    py::class_<bkt::SessionManager>(m_bkt, "SessionManager")
        .def(py::init<>());

    // Módulo MAB
    py::module_ m_mab = m.def_submodule("mab", "MAB Module");

    py::enum_<mab::METHOD>(m_mab, "METHOD")
        .value("VISUAL", mab::METHOD::VISUAL)
        .value("AUDITORY", mab::METHOD::AUDITORY)
        .value("KINESTHETIC", mab::METHOD::KINESTHETIC)
        .value("PHONETIC", mab::METHOD::PHONETIC)
        .value("GLOBAL", mab::METHOD::GLOBAL)
        .export_values();

    py::class_<mab::MABEngine>(m_mab, "MABEngine")
        .def(py::init<double>(), py::arg("exploration_c") = 1.0);

    // Módulo Zone
    py::module_ m_zone = m.def_submodule("zone", "Zone Module");

    py::enum_<zone::Zone>(m_zone, "Zone")
        .value("LOW", zone::Zone::LOW)
        .value("CURRENT", zone::Zone::CURRENT)
        .export_values();

    py::class_<zone::ZoneBlender>(m_zone, "ZoneBlender")
        .def(py::init<uint64_t>(), py::arg("seed") = 0);

    // Módulo Graph
    py::module_ m_graph = m.def_submodule("graph", "Graph Module");

    py::class_<graph::SkillGraph>(m_graph, "SkillGraph")
        .def(py::init<>())
        .def("load", &graph::SkillGraph::load)
        .def("get_prerequisites", &graph::SkillGraph::getPrerequisites)
        .def("get_unlocked_skills", &graph::SkillGraph::getUnlockedSkills)
        .def("exists", &graph::SkillGraph::exists)
        .def("size", &graph::SkillGraph::size);

    // Módulo SRS
    py::module_ m_srs = m.def_submodule("srs", "SRS Module");

    py::class_<srs::SRSQueue>(m_srs, "SRSQueue")
        .def(py::init<>())
        .def("mark_result", &srs::SRSQueue::markResult)
        .def("get_due_skills", &srs::SRSQueue::getDueSkills);

    // Módulo Persistence
    py::module_ m_persistence = m.def_submodule("persistence", "Persistence Module");

    py::class_<persistence::PersistenceLayer, 
               std::unique_ptr<persistence::PersistenceLayer>>(m_persistence, "PersistenceLayer")
        .def_static("create", &persistence::PersistenceLayer::create)
        // Ya no atamos init, pero debemos decirle a pybind11 que maneje unique_ptr
        .def("load_skill_state", [](persistence::PersistenceLayer& self, int student_id, int skill_id) {
             return self.loadSkillState(student_id, skill_id);
         });

    // Módulo Core
    py::module_ m_core = m.def_submodule("core", "Core Module");

    py::class_<core::ResponseResult>(m_core, "ResponseResult")
        .def_readonly("next_method", &core::ResponseResult::next_method)
        .def_readonly("next_zone", &core::ResponseResult::next_zone)
        .def_readonly("current_pL", &core::ResponseResult::current_pL)
        .def_readonly("was_anomalous", &core::ResponseResult::was_anomalous)
        .def_readonly("valid_skill", &core::ResponseResult::valid_skill);

    py::class_<core::ResponseProcessor>(m_core, "ResponseProcessor")
        .def(py::init<bkt::BKTEngine&, mab::MABEngine&, bkt::SessionManager&,
                      persistence::PersistenceLayer&, zone::ZoneBlender&,
                      graph::SkillGraph&, srs::SRSQueue&, double>(),
             py::arg("bkt"), py::arg("mab"), py::arg("session"),
             py::arg("storage"), py::arg("blender"), py::arg("skill_graph"),
             py::arg("srs_queue"), py::arg("lambda_val") = 0.5)
        .def("process_response", &core::ResponseProcessor::processResponse,
             py::arg("student_id"), py::arg("skill_id"), py::arg("used_method"),
             py::arg("correct"), py::arg("response_ms"))
        .def("start_session", &core::ResponseProcessor::startSession)
        .def("end_session", &core::ResponseProcessor::endSession)
        .def("get_due_skills", &core::ResponseProcessor::getDueSkills)
        .def("get_unlocked_skills", &core::ResponseProcessor::getUnlockedSkills);
}
