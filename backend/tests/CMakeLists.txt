add_executable(hestia_tests main.cpp) # Crea un main.cpp simple en tests/
target_link_libraries(hestia_tests PRIVATE hestia_backend)
add_test(NAME HestiaTests COMMAND hestia_tests)
