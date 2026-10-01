# Lab 0: Pre-Flight Environment Bootstrap

Welcome to the Multi-Domain AI Workshop! Before diving into the operational scenarios, you must configure your assigned Google Cloud Project.

This lab will guide you through setting up Cloud Shell, importing the repository files from the shared Google Workspace Drive, and bootstrapping the foundation infrastructure using the automated setup script.

---

## 1. Google Cloud Console Access & Verification

1. Open Chrome and navigate to the [Google Cloud Console](https://console.cloud.google.com).
2. Log in using the Customer credentials provided by the instructor.
3. In the top-left project drop-down menu, ensure you have selected your assigned Google Cloud Project (e.g., `learning-lab-project-xyz`).

## 2. Launch Cloud Shell Editor

We will use Google Cloud Shell as our primary development environment. Cloud Shell provides a browser-based terminal and an integrated IDE (Code Editor) pre-loaded with Python, `gcloud`, and other essential tools.

1. Click the **Activate Cloud Shell** icon (`>_`) in the top-right corner of the Google Cloud Console toolbar.
2. Wait a few moments for the Cloud Shell instance to provision and connect.
3. Once the terminal opens at the bottom of your screen, click the **Open Editor** button on the Cloud Shell toolbar to launch the integrated Code Editor.
4. Your browser will split into two panes: the Code Editor on top and the Terminal at the bottom.

## 3. Upload Repository Files

The instructor has provided a shared Google Workspace Drive link containing the folder structure of the repository.

1. Navigate to **Shared with me** in your Google Workspace Drive and download the `Learning Labs` folder to your local machine.
2. In the Cloud Shell Editor pane, right-click in the empty space of the Explorer (left sidebar) and select **Upload Folder...**
3. Select the `Learning Labs` folder you just downloaded.
4. Wait for the upload to complete. You should now see the `Learning Labs` folder in your Cloud Shell Explorer.
5. In your Cloud Shell terminal, change directories into the repository root:
   ```bash
   cd "Learning Labs"
   ```

## 4. Execute Automated Bootstrap

The `lab0/code` folder contains an automated `setup.sh` script that provisions IAM service accounts, enables required APIs (BigQuery, Vertex AI, Agent Registry, Cloud Run), and initializes the core environment variables.

1. In your Cloud Shell terminal, navigate into the Lab 0 code directory:
   ```bash
   cd lab0/code
   ```
2. Make the script executable:
   ```bash
   chmod +x setup.sh
   ```
3. Execute the setup script:
   ```bash
   ./setup.sh
   ```
4. **Observe the Output**: The script will verify your Python version, authenticate your `gcloud` credentials, enable APIs, and initialize a local SQLite database for Lab 2. When finished, it will print a summary of the configuration.

## 5. Verify ADK Web Environment

To ensure your environment is fully operational, we will briefly test the Agent Developer Kit (ADK) web interface, which we will use extensively in upcoming labs.

1. From the repository root (`Learning Labs`), start the ADK Web interface:
   ```bash
   cd ../..
   adk web
   ```
2. In the Cloud Shell terminal, click the **Web Preview** icon (it looks like an eye) in the top-right corner and select **Preview on port 8080**.
3. The ADK Chat UI should load in a new browser tab.
4. Once you have verified the UI loads, return to the terminal and press `Ctrl+C` to stop the server.

---

### 🎉 Success!
Your environment is successfully initialized, and the infrastructure is ready. You may now proceed to **Lab 1: Data Foundations & Multi-Domain Intelligence**.
