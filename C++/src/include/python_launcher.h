#ifndef PYTHON_LAUNCHER_H
#define PYTHON_LAUNCHER_H

#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <chrono>
#include <unistd.h>
#include <sys/wait.h>
#include <signal.h>

namespace trading {

/**
 * @brief Manages Python subprocess lifecycle for the trading system
 *
 * This class provides robust process management for Python scripts,
 * including health monitoring, graceful shutdown, and error recovery.
 * Designed for high-reliability trading applications.
 */
class PythonLauncher {
public:
    /**
     * @brief Process state enumeration
     */
    enum class ProcessState {
        NOT_STARTED,    ///< Process hasn't been launched yet
        RUNNING,        ///< Process is actively running
        TERMINATED,     ///< Process terminated normally
        CRASHED,        ///< Process terminated unexpectedly
        FAILED_TO_START ///< Process failed to launch
    };

    /**
     * @brief Configuration for Python process
     */
    struct Config {
        std::string script_path;                    ///< Path to Python script
        std::string python_executable = "python3"; ///< Python interpreter path
        std::vector<std::string> arguments;         ///< Command line arguments
        std::string working_directory = ".";        ///< Working directory for script
        std::chrono::seconds startup_timeout{5};    ///< Max time to wait for startup
        std::chrono::seconds shutdown_timeout{10};  ///< Max time for graceful shutdown
        bool auto_restart = false;                  ///< Automatically restart on crash
        int max_restart_attempts = 3;               ///< Maximum restart attempts
    };

    /**
     * @brief Callback function type for process events
     * @param pid Process ID
     * @param exit_code Exit code (if terminated)
     */
    using ProcessCallback = std::function<void(pid_t pid, int exit_code)>;

private:
    Config config_;
    pid_t process_pid_;
    ProcessState state_;
    int restart_count_;
    std::chrono::steady_clock::time_point start_time_;

    // Event callbacks
    ProcessCallback on_started_;
    ProcessCallback on_terminated_;
    ProcessCallback on_crashed_;

    // Internal helper methods
    bool validate_config() const;
    std::vector<char*> build_exec_args() const;
    bool wait_for_startup();
    void update_process_state();
    void handle_process_exit(int exit_code);

public:
    /**
     * @brief Construct launcher with configuration
     * @param config Process configuration
     */
    explicit PythonLauncher(const Config& config);

    /**
     * @brief Construct launcher with simple script path
     * @param script_path Path to Python script
     */
    explicit PythonLauncher(const std::string& script_path);

    /**
     * @brief Destructor ensures clean shutdown
     */
    ~PythonLauncher();

    // Disable copy operations (process management should be unique)
    PythonLauncher(const PythonLauncher&) = delete;
    PythonLauncher& operator=(const PythonLauncher&) = delete;

    // Enable move operations
    PythonLauncher(PythonLauncher&& other) noexcept;
    PythonLauncher& operator=(PythonLauncher&& other) noexcept;

    /**
     * @brief Start the Python process
     * @return true if process started successfully
     */
    bool start();

    /**
     * @brief Stop the Python process gracefully
     * @param force_kill If true, use SIGKILL if graceful shutdown fails
     * @return true if process stopped successfully
     */
    bool stop(bool force_kill = true);

    /**
     * @brief Restart the Python process
     * @return true if restart successful
     */
    bool restart();

    /**
     * @brief Check if process is currently running
     * @return true if process is active
     */
    bool is_running() const;

    /**
     * @brief Get current process state
     * @return Current ProcessState
     */
    ProcessState get_state() const { return state_; }

    /**
     * @brief Get process ID (if running)
     * @return Process ID or -1 if not running
     */
    pid_t get_pid() const { return process_pid_; }

    /**
     * @brief Get process uptime
     * @return Duration since process started
     */
    std::chrono::steady_clock::duration get_uptime() const;

    /**
     * @brief Update process state (call periodically from main loop)
     * This method checks if the process is still alive and updates internal state
     */
    void update();

    /**
     * @brief Send signal to the Python process
     * @param signal Signal to send (e.g., SIGTERM, SIGUSR1)
     * @return true if signal sent successfully
     */
    bool send_signal(int signal) const;

    /**
     * @brief Set callback for process started event
     * @param callback Function to call when process starts
     */
    void set_started_callback(ProcessCallback callback) {
        on_started_ = std::move(callback);
    }

    /**
     * @brief Set callback for process terminated event
     * @param callback Function to call when process terminates normally
     */
    void set_terminated_callback(ProcessCallback callback) {
        on_terminated_ = std::move(callback);
    }

    /**
     * @brief Set callback for process crashed event
     * @param callback Function to call when process crashes
     */
    void set_crashed_callback(ProcessCallback callback) {
        on_crashed_ = std::move(callback);
    }

    /**
     * @brief Get human-readable state string
     * @return String representation of current state
     */
    std::string get_state_string() const;

    /**
     * @brief Get restart count
     * @return Number of times process has been restarted
     */
    int get_restart_count() const { return restart_count_; }
};

/**
 * @brief Factory function to create launcher for trading Python scripts
 * @param script_name Name of the Python script (assumes it's in ../Python/)
 * @return Configured PythonLauncher instance
 */
std::unique_ptr<PythonLauncher> create_trading_python_launcher(
    const std::string& script_name);

/**
 * @brief RAII helper for managing multiple Python processes
 *
 * Useful when you need to coordinate multiple Python components
 * (e.g., data consumer, ML inference, risk monitor)
 */
class PythonProcessManager {
private:
    std::vector<std::unique_ptr<PythonLauncher>> launchers_;
    bool all_running_;

public:
    /**
     * @brief Add a Python launcher to be managed
     * @param launcher Unique pointer to launcher
     */
    void add_launcher(std::unique_ptr<PythonLauncher> launcher);

    /**
     * @brief Start all managed processes
     * @return true if all processes started successfully
     */
    bool start_all();

    /**
     * @brief Stop all managed processes
     * @param force_kill Use SIGKILL if graceful shutdown fails
     */
    void stop_all(bool force_kill = true);

    /**
     * @brief Check if all processes are running
     * @return true if all processes are active
     */
    bool all_running() const;

    /**
     * @brief Update all process states
     */
    void update_all();

    /**
     * @brief Get count of running processes
     * @return Number of currently running processes
     */
    size_t running_count() const;

    /**
     * @brief Get total number of managed processes
     * @return Total process count
     */
    size_t total_count() const { return launchers_.size(); }

    /**
     * @brief Destructor stops all processes
     */
    ~PythonProcessManager() { stop_all(); }
};

} // namespace trading

#endif // PYTHON_LAUNCHER_H