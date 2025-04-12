import sys
import os
import json
import requests
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QPushButton,
    QFileDialog,
    QListWidget,
    QMessageBox,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QIcon

class GitHubIssueGenerator:
    def __init__(self, token=None, owner=None, repo=None):
        """
        Initialise le générateur d'issues GitHub.

        Args:
            token (str): Token d'accès personnel GitHub
            owner (str): Propriétaire du dépôt (username ou organisation)
            repo (str): Nom du dépôt
        """
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.owner = owner
        self.repo = repo

    def get_base_url(self):
        return f"https://api.github.com/repos/{self.owner}/{self.repo}"

    def get_headers(self):
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def create_issue(self, title, body, labels=None, assignees=None, issue_type=None):
        """
        Crée une nouvelle issue sur GitHub.

        Args:
            title (str): Titre de l'issue
            body (str): Description de l'issue
            labels (list): Liste des labels à appliquer
            assignees (list): Liste des utilisateurs assignés
            issue_type (str): Type de l'issue (Bug, Feature, Task)

        Returns:
            dict: Réponse de l'API GitHub
        """
        if not self.token:
            raise ValueError("GitHub token requis.")

        if not self.owner or not self.repo:
            raise ValueError("Propriétaire et nom du dépôt requis.")

        url = f"{self.get_base_url()}/issues"

        data = {"title": title, "body": body}

        if labels:
            data["labels"] = labels

        if assignees:
            data["assignees"] = assignees

        if issue_type:
            data["type"] = issue_type 

        response = requests.post(url, headers=self.get_headers(), json=data)

        if response.status_code == 201:
            return response.json(), True
        else:
            return response.text, False

    def list_issues(self, state="open"):
        """
        Liste les issues du dépôt.

        Args:
            state (str): État des issues (open, closed, all)

        Returns:
            list: Liste des issues
        """
        if not self.token or not self.owner or not self.repo:
            return [], False

        url = f"{self.get_base_url()}/issues"
        params = {"state": state}

        response = requests.get(url, headers=self.get_headers(), params=params)

        if response.status_code == 200:
            return response.json(), True
        else:
            return response.text, False

    def create_issues_from_list(self, issues_data):
        """
        Crée des issues à partir d'une liste de dictionnaires.

        Args:
            issues_data (list): Liste des données d'issues

        Returns:
            list: Liste des issues créées
        """
        if not issues_data:
            return [], False

        results = []
        success = True

        for issue in issues_data:
            result, status = self.create_issue(
                title=issue.get("title", ""),
                body=issue.get("body", ""),
                labels=issue.get("labels", []),
                assignees=issue.get("assignees", []),
            )
            if status:
                results.append(result)
            else:
                success = False
                results.append({"error": result, "issue": issue})

        return results, success

    def get_labels(self):
        """Récupère les labels disponibles dans le dépôt"""
        if not self.token or not self.owner or not self.repo:
            return [], False

        url = f"{self.get_base_url()}/labels"

        response = requests.get(url, headers=self.get_headers())

        if response.status_code == 200:
            return response.json(), True
        else:
            return response.text, False

    def get_collaborators(self):
        """Récupère les collaborateurs du dépôt"""
        if not self.token or not self.owner or not self.repo:
            return [], False

        url = f"{self.get_base_url()}/collaborators"

        response = requests.get(url, headers=self.get_headers())

        if response.status_code == 200:
            return response.json(), True
        else:
            return response.text, False

    def verify_credentials(self):
        """Vérifie si les identifiants sont valides"""
        if not self.token or not self.owner or not self.repo:
            return False

        url = f"{self.get_base_url()}"
        response = requests.get(url, headers=self.get_headers())

        return response.status_code == 200


class GithubIssueGeneratorGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Générateur d'Issues GitHub")
        self.setMinimumSize(800, 600)

        app_icon = QIcon("assets/logo.ico")
        self.setWindowIcon(app_icon)

        # Initialisation des variables
        self.issue_generator = GitHubIssueGenerator()
        self.settings = QSettings("IssueGenerator", "GitHubIssues")
        self.bulk_issues = []

        self.token_history = (
            self.settings.value("token_history", []) or []
        )  # Ajout de l'historique

        # Configuration de l'interface (doit être appelé avant d'utiliser self.tabs)
        self.setup_ui()

        # Charger les paramètres sauvegardés
        self.load_settings()

        # Définir une police moderne
        font = self.font()
        font.setFamily("Segoe UI")
        font.setPointSize(9)
        self.setFont(font)

        # Définir les icônes pour les onglets (maintenant que self.tabs existe)
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setDocumentMode(True)

        # Modifier les boutons de template
        for btn in [
            self.bug_template_btn,
            self.feature_template_btn,
            self.doc_template_btn,
        ]:
            btn.setMinimumWidth(120)
            btn.setMinimumHeight(32)

        # Améliorer le tableau des issues
        self.issues_table.setAlternatingRowColors(True)
        self.issues_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.issues_table.setShowGrid(True)

        # Améliorer la mise en page des formulaires
        for input_widget in [self.title_input, self.labels_input, self.assignees_input]:
            input_widget.setMinimumHeight(32)

        self.body_input.setMinimumHeight(200)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                padding: 8px 16px;
                background: #e0e0e0;
                border: 1px solid #cccccc;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: white;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QLineEdit, QTextEdit {
                padding: 6px;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QTableWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 6px;
                border: none;
                border-right: 1px solid #cccccc;
                border-bottom: 1px solid #cccccc;
            }
            QGroupBox {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)

    def setup_ui(self):
        # Widget central et layout principal
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # Onglets
        self.tabs = QTabWidget()

        # Onglet de connexion
        connection_tab = QWidget()
        connection_layout = QVBoxLayout(connection_tab)

        # Formulaire de connexion
        connection_form = QFormLayout()

        # Création du combo box pour les tokens
        self.token_combo = QComboBox()
        self.token_combo.setEditable(True)
        self.token_combo.setMaxVisibleItems(5)
        self.token_combo.addItems(self.token_history)
        self.token_combo.setCurrentText(self.issue_generator.token or "")
        self.token_combo.setInsertPolicy(QComboBox.InsertAtTop)
        self.token_combo.lineEdit().setPlaceholderText("Entrez votre token GitHub")
        self.token_combo.lineEdit().setEchoMode(QLineEdit.Password)

        # Champs propriétaire et dépôt
        self.owner_input = QLineEdit(self.issue_generator.owner or "")
        self.owner_input.setPlaceholderText(
            "Propriétaire du dépôt (username ou organisation)"
        )

        self.repo_input = QLineEdit(self.issue_generator.repo or "")
        self.repo_input.setPlaceholderText("Nom du dépôt")

        # Bouton pour effacer l'historique
        clear_history_button = QPushButton("Effacer l'historique")
        clear_history_button.clicked.connect(self.clear_token_history)

        # Layout pour le token et le bouton d'effacement
        token_layout = QHBoxLayout()
        token_layout.addWidget(self.token_combo)
        token_layout.addWidget(clear_history_button)

        # Ajout des champs au formulaire
        connection_form.addRow("Token GitHub:", token_layout)
        connection_form.addRow("Propriétaire:", self.owner_input)
        connection_form.addRow("Dépôt:", self.repo_input)

        # Bouton de connexion
        self.connect_button = QPushButton("Vérifier la connexion")
        self.connect_button.clicked.connect(self.verify_connection)

        connection_layout.addLayout(connection_form)
        connection_layout.addWidget(self.connect_button)
        connection_layout.addStretch()

        # Onglet de création d'issue
        create_tab = QWidget()
        create_layout = QVBoxLayout(create_tab)

        # Formulaire de création
        create_form = QFormLayout()

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Titre de l'issue")

        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText("Description de l'issue")

        self.labels_input = QLineEdit()
        self.labels_input.setPlaceholderText("Labels séparés par des virgules")

        self.assignees_input = QLineEdit()
        self.assignees_input.setPlaceholderText("Assignés séparés par des virgules")

        create_form.addRow("Titre:", self.title_input)
        create_form.addRow("Description:", self.body_input)
        create_form.addRow("Labels:", self.labels_input)
        create_form.addRow("Assignés:", self.assignees_input)

        # Boutons pour les modèles
        templates_box = QGroupBox("Modèles")
        templates_layout = QHBoxLayout(templates_box)

        self.bug_template_btn = QPushButton("Bug")
        self.feature_template_btn = QPushButton("Fonctionnalité")
        self.doc_template_btn = QPushButton("Documentation")

        self.bug_template_btn.clicked.connect(lambda: self.load_template("bug"))
        self.feature_template_btn.clicked.connect(lambda: self.load_template("feature"))
        self.doc_template_btn.clicked.connect(
            lambda: self.load_template("documentation")
        )

        templates_layout.addWidget(self.bug_template_btn)
        templates_layout.addWidget(self.feature_template_btn)
        templates_layout.addWidget(self.doc_template_btn)

        # Bouton de création
        self.create_button = QPushButton("Créer l'issue")
        self.create_button.clicked.connect(self.create_issue)

        create_layout.addLayout(create_form)
        create_layout.addWidget(templates_box)
        create_layout.addWidget(self.create_button)

        # Onglet de liste d'issues
        list_tab = QWidget()
        list_layout = QVBoxLayout(list_tab)

        # Contrôles de filtre
        filter_layout = QHBoxLayout()

        self.state_combo = QComboBox()
        self.state_combo.addItems(["ouvertes", "fermées", "toutes"])

        self.refresh_button = QPushButton("Rafraîchir")
        self.refresh_button.clicked.connect(self.refresh_issues)

        filter_layout.addWidget(QLabel("État:"))
        filter_layout.addWidget(self.state_combo)
        filter_layout.addWidget(self.refresh_button)
        filter_layout.addStretch()

        # Tableau des issues
        self.issues_table = QTableWidget()
        self.issues_table.setColumnCount(4)
        self.issues_table.setHorizontalHeaderLabels(["#", "Titre", "État", "URL"])
        self.issues_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        self.issues_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.Stretch
        )

        list_layout.addLayout(filter_layout)
        list_layout.addWidget(self.issues_table)

        # Onglet de création en masse
        bulk_tab = QWidget()
        bulk_layout = QVBoxLayout(bulk_tab)

        # Contrôles de fichier
        file_layout = QHBoxLayout()

        self.load_file_button = QPushButton("Charger un fichier JSON")
        self.load_file_button.clicked.connect(self.load_json_file)

        self.save_file_button = QPushButton("Sauvegarder en JSON")
        self.save_file_button.clicked.connect(self.save_json_file)

        file_layout.addWidget(self.load_file_button)
        file_layout.addWidget(self.save_file_button)
        file_layout.addStretch()

        # Liste des issues en masse
        self.bulk_list = QListWidget()
        self.bulk_list.itemDoubleClicked.connect(self.edit_bulk_issue)

        # Contrôles d'édition
        edit_layout = QHBoxLayout()

        self.add_bulk_button = QPushButton("Ajouter")
        self.add_bulk_button.clicked.connect(self.add_bulk_issue)

        self.remove_bulk_button = QPushButton("Supprimer")
        self.remove_bulk_button.clicked.connect(self.remove_bulk_issue)

        self.create_bulk_button = QPushButton("Créer toutes les issues")
        self.create_bulk_button.clicked.connect(self.create_bulk_issues)

        edit_layout.addWidget(self.add_bulk_button)
        edit_layout.addWidget(self.remove_bulk_button)
        edit_layout.addWidget(self.create_bulk_button)

        bulk_layout.addLayout(file_layout)
        bulk_layout.addWidget(self.bulk_list)
        bulk_layout.addLayout(edit_layout)

        # Ajouter les onglets
        self.tabs.addTab(connection_tab, "Connexion")
        self.tabs.addTab(create_tab, "Créer une issue")
        self.tabs.addTab(list_tab, "Lister les issues")
        self.tabs.addTab(bulk_tab, "Création en masse")

        # Désactiver les onglets jusqu'à la vérification
        self.tabs.setTabEnabled(1, False)
        self.tabs.setTabEnabled(2, False)
        self.tabs.setTabEnabled(3, False)

        # Ajouter les onglets au layout principal
        main_layout.addWidget(self.tabs)

        # Barre de statut
        self.statusBar().showMessage("Prêt")

        # Définir le widget central
        self.setCentralWidget(central_widget)

    def load_settings(self):
        # Charger les paramètres sauvegardés
        token = self.settings.value("token", "")
        owner = self.settings.value("owner", "")
        repo = self.settings.value("repo", "")
        self.token_history = self.settings.value("token_history", []) or []

        self.issue_generator.token = token
        self.issue_generator.owner = owner
        self.issue_generator.repo = repo

    def clear_token_history(self):
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Voulez-vous vraiment effacer l'historique des tokens ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.token_history = []
            self.token_combo.clear()
            self.settings.setValue("token_history", [])
            self.token_combo.setCurrentText("")
            self.statusBar().showMessage("Historique des tokens effacé")

    def save_settings(self):
        # Sauvegarder les paramètres
        self.settings.setValue("token", self.issue_generator.token)
        self.settings.setValue("owner", self.issue_generator.owner)
        self.settings.setValue("repo", self.issue_generator.repo)

    def verify_connection(self):
        # Mettre à jour les variables
        token = self.token_combo.currentText().strip()
        self.issue_generator.token = (
            token  # Utiliser token_combo au lieu de token_input
        )
        self.issue_generator.owner = self.owner_input.text().strip()
        self.issue_generator.repo = self.repo_input.text().strip()

        # Vérifier si les champs sont remplis
        if not self.issue_generator.token:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un token GitHub.")
            return

        if not self.issue_generator.owner:
            QMessageBox.warning(
                self, "Erreur", "Veuillez entrer le propriétaire du dépôt."
            )
            return

        if not self.issue_generator.repo:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer le nom du dépôt.")
            return

        # Vérifier la connexion
        self.statusBar().showMessage("Vérification de la connexion...")

        try:
            if self.issue_generator.verify_credentials():
                if token not in self.token_history:
                    self.token_history.insert(0, token)
                    # Garder uniquement les 5 derniers tokens
                    self.token_history = self.token_history[:5]
                    # Mettre à jour le combo box
                    self.token_combo.clear()
                    self.token_combo.addItems(self.token_history)
                    # Sauvegarder l'historique
                    self.settings.setValue("token_history", self.token_history)

                QMessageBox.information(
                    self, "Succès", "Connexion établie avec succès!"
                )
                self.save_settings()

                # Activer les onglets
                self.tabs.setTabEnabled(1, True)
                self.tabs.setTabEnabled(2, True)
                self.tabs.setTabEnabled(3, True)

                # Aller à l'onglet de création
                self.tabs.setCurrentIndex(1)

                self.statusBar().showMessage(
                    "Connecté à "
                    + self.issue_generator.owner
                    + "/"
                    + self.issue_generator.repo
                )
            else:
                QMessageBox.warning(
                    self,
                    "Erreur",
                    "Impossible de se connecter. Vérifiez vos informations.",
                )
                self.statusBar().showMessage("Erreur de connexion")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue: {str(e)}")
            self.statusBar().showMessage("Erreur: " + str(e))

    def load_template(self, template_type):
        templates = {
        "bug": {
            "title": "[Bug] ",
            "body": """## Description du bug
Décrivez clairement et précisément le bug rencontré.

## Étapes pour reproduire
1. 
2. 
3. 

## Comportement attendu
Décrivez ce qui devrait se passer normalement.

## Comportement actuel 
Décrivez ce qui se passe actuellement.

## Environnement
- OS: [ex: Windows 10]
- Navigateur: [ex: Chrome 96]
- Version: [ex: 1.0.0]

## Captures d'écran
Si applicable, ajoutez des captures d'écran pour illustrer le problème.

## Logs d'erreur
```
Collez ici les logs d'erreur si disponibles
```

## Informations supplémentaires
Tout autre contexte utile pour comprendre et résoudre le bug.""",
            "labels": "bug",
            "type": "Bug",
            "assignees": "",
        },
        "feature": {
            "title": "[Feature] ",
            "body": """## User Story
En tant que [type d'utilisateur]
Je veux [action/fonctionnalité souhaitée]
Afin de [bénéfice/objectif]

## Solution technique proposée
Décrivez en détail comment la fonctionnalité devrait être implémentée.

## Informations supplémentaires
Tout autre contexte ou capture d'écran utile.""",
            "labels": "enhancement",
            "type": "Feature",
            "assignees": "",
        },
        "documentation": {
            "title": "[Documentation] ",
            "body": """## Description
Décrivez ce qui doit être documenté ou les modifications à apporter.

## Sections concernées
- Section 1
- Section 2

## Modifications proposées
Détaillez les changements/ajouts à apporter à la documentation.

## Points à couvrir
- [ ] Point 1
- [ ] Point 2
- [ ] Point 3

## Ressources utiles
- Lien 1
- Lien 2

## Informations supplémentaires
Tout autre contexte pertinent.""",
            "labels": "documentation",
            "type": "Task",
            "assignees": "",
        },
    }

        template = templates.get(template_type)
        if template:
            self.title_input.setText(template["title"])
            self.body_input.setText(template["body"])
            self.labels_input.setText(template["labels"])
            self.assignees_input.setText(template["assignees"])
            self.current_issue_type = template["type"]

    def create_issue(self):
        # Récupérer les valeurs
        title = self.title_input.text().strip()
        body = self.body_input.toPlainText().strip()
        labels_text = self.labels_input.text().strip()
        assignees_text = self.assignees_input.text().strip()

        # Convertir les chaînes en listes
        labels = [label.strip() for label in labels_text.split(",")] if labels_text else []
        assignees = [assignee.strip() for assignee in assignees_text.split(",")] if assignees_text else []

        # Créer l'issue
        self.statusBar().showMessage("Création de l'issue...")

        try:
            result, success = self.issue_generator.create_issue(
                title, body, labels, assignees, issue_type=self.current_issue_type
            )

            if success:
                QMessageBox.information(
                    self,
                    "Succès",
                    f"Issue créée avec succès!\nURL: {result['html_url']}",
                )
                self.statusBar().showMessage("Issue créée: " + result["html_url"])
            else:
                QMessageBox.warning(
                    self, "Erreur", f"Impossible de créer l'issue: {result}"
                )
                self.statusBar().showMessage("Erreur lors de la création de l'issue")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue: {str(e)}")
            self.statusBar().showMessage("Erreur: " + str(e))

    def refresh_issues(self):
        # Récupérer l'état sélectionné
        state_map = {"ouvertes": "open", "fermées": "closed", "toutes": "all"}
        state = state_map[self.state_combo.currentText()]

        # Récupérer les issues
        self.statusBar().showMessage("Récupération des issues...")

        try:
            issues, success = self.issue_generator.list_issues(state)

            if success:
                # Effacer le tableau
                self.issues_table.setRowCount(0)

                # Remplir le tableau
                for i, issue in enumerate(issues):
                    self.issues_table.insertRow(i)

                    # Numéro
                    num_item = QTableWidgetItem(str(issue["number"]))
                    num_item.setTextAlignment(Qt.AlignCenter)
                    self.issues_table.setItem(i, 0, num_item)

                    # Titre
                    self.issues_table.setItem(i, 1, QTableWidgetItem(issue["title"]))

                    # État
                    state_item = QTableWidgetItem(issue["state"])
                    state_item.setTextAlignment(Qt.AlignCenter)
                    self.issues_table.setItem(i, 2, state_item)

                    # URL
                    url_item = QTableWidgetItem(issue["html_url"])
                    url_item.setTextAlignment(Qt.AlignCenter)
                    self.issues_table.setItem(i, 3, url_item)

                self.statusBar().showMessage(f"{len(issues)} issues récupérées")
            else:
                QMessageBox.warning(
                    self, "Erreur", f"Impossible de récupérer les issues: {issues}"
                )
                self.statusBar().showMessage(
                    "Erreur lors de la récupération des issues"
                )
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue: {str(e)}")
            self.statusBar().showMessage("Erreur: " + str(e))

    def add_bulk_issue(self):
        # Créer une nouvelle issue en masse
        title = "Nouvelle issue"
        body = "Description de l'issue"
        labels = []
        assignees = []

        # Ajouter à la liste
        issue_data = {
            "title": title,
            "body": body,
            "labels": labels,
            "assignees": assignees,
        }

        self.bulk_issues.append(issue_data)

        # Mettre à jour la liste
        self.update_bulk_list()

        # Éditer l'issue
        self.edit_bulk_issue(self.bulk_list.item(len(self.bulk_issues) - 1))

    def remove_bulk_issue(self):
        # Récupérer l'index sélectionné
        current_row = self.bulk_list.currentRow()

        if current_row >= 0:
            # Supprimer l'issue
            del self.bulk_issues[current_row]

            # Mettre à jour la liste
            self.update_bulk_list()

    def edit_bulk_issue(self, item):
        # Récupérer l'index
        index = self.bulk_list.row(item)

        if index >= 0 and index < len(self.bulk_issues):
            issue_data = self.bulk_issues[index]

            # Créer une boîte de dialogue d'édition
            dialog = QWidget(self, Qt.Dialog)
            dialog.setWindowTitle("Éditer l'issue")
            dialog.setMinimumWidth(500)

            # Layout
            layout = QVBoxLayout(dialog)

            # Formulaire
            form = QFormLayout()

            title_input = QLineEdit(issue_data["title"])
            body_input = QTextEdit()
            body_input.setText(issue_data["body"])

            labels_input = QLineEdit(",".join(issue_data["labels"]))
            assignees_input = QLineEdit(",".join(issue_data["assignees"]))

            form.addRow("Titre:", title_input)
            form.addRow("Description:", body_input)
            form.addRow("Labels:", labels_input)
            form.addRow("Assignés:", assignees_input)

            # Boutons
            buttons_layout = QHBoxLayout()

            save_button = QPushButton("Enregistrer")
            cancel_button = QPushButton("Annuler")

            buttons_layout.addWidget(save_button)
            buttons_layout.addWidget(cancel_button)

            # Connecter les signaux
            save_button.clicked.connect(
                lambda: self.save_bulk_issue(
                    index,
                    title_input.text(),
                    body_input.toPlainText(),
                    labels_input.text(),
                    assignees_input.text(),
                    dialog,
                )
            )
            cancel_button.clicked.connect(dialog.close)

            # Ajouter les layouts
            layout.addLayout(form)
            layout.addLayout(buttons_layout)

            # Afficher la boîte de dialogue
            dialog.show()

    def save_bulk_issue(self, index, title, body, labels_text, assignees_text, dialog):
        # Convertir les chaînes en listes
        labels = (
            [label.strip() for label in labels_text.split(",")] if labels_text else []
        )
        assignees = (
            [assignee.strip() for assignee in assignees_text.split(",")]
            if assignees_text
            else []
        )

        # Mettre à jour l'issue
        self.bulk_issues[index]["title"] = title
        self.bulk_issues[index]["body"] = body
        self.bulk_issues[index]["labels"] = labels
        self.bulk_issues[index]["assignees"] = assignees

        # Mettre à jour la liste
        self.update_bulk_list()

        # Fermer la boîte de dialogue
        dialog.close()

    def update_bulk_list(self):
        # Effacer la liste
        self.bulk_list.clear()

        # Remplir la liste
        for issue in self.bulk_issues:
            self.bulk_list.addItem(issue["title"])

    def load_json_file(self):
        # Ouvrir un fichier JSON
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Ouvrir un fichier JSON", "", "Fichiers JSON (*.json)"
        )

        if file_path:
            try:
                # Charger le fichier
                with open(file_path, "r", encoding="utf-8") as file:
                    self.bulk_issues = json.load(file)

                # Mettre à jour la liste
                self.update_bulk_list()

                self.statusBar().showMessage(
                    f"{len(self.bulk_issues)} issues chargées depuis {file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Erreur", f"Impossible de charger le fichier: {str(e)}"
                )
                self.statusBar().showMessage("Erreur lors du chargement du fichier")

    def save_json_file(self):
        # Enregistrer un fichier JSON
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer un fichier JSON", "", "Fichiers JSON (*.json)"
        )

        if file_path:
            try:
                # Enregistrer le fichier
                with open(file_path, "w", encoding="utf-8") as file:
                    json.dump(self.bulk_issues, file, indent=2)

                self.statusBar().showMessage(
                    f"{len(self.bulk_issues)} issues enregistrées dans {file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Erreur", f"Impossible d'enregistrer le fichier: {str(e)}"
                )
                self.statusBar().showMessage(
                    "Erreur lors de l'enregistrement du fichier"
                )

    def create_bulk_issues(self):
        # Vérifier s'il y a des issues
        if not self.bulk_issues:
            QMessageBox.warning(self, "Attention", "Aucune issue à créer.")
            return

        # Demander confirmation
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Voulez-vous créer {len(self.bulk_issues)} issues?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # Créer les issues
            self.statusBar().showMessage("Création des issues...")

            try:
                results, success = self.issue_generator.create_issues_from_list(
                    self.bulk_issues
                )

                if success:
                    QMessageBox.information(
                        self, "Succès", f"{len(results)} issues créées avec succès!"
                    )

                    # Effacer la liste
                    self.bulk_issues = []
                    self.update_bulk_list()

                    self.statusBar().showMessage(f"{len(results)} issues créées")
                else:
                    error_message = "Erreurs lors de la création des issues:\n"
                    for result in results:
                        if "error" in result:
                            error_message += (
                                f"- {result['issue']['title']}: {result['error']}\n"
                            )

                    QMessageBox.warning(self, "Erreur", error_message)
                    self.statusBar().showMessage(
                        "Erreurs lors de la création des issues"
                    )
            except Exception as e:
                QMessageBox.critical(
                    self, "Erreur", f"Une erreur est survenue: {str(e)}"
                )
                self.statusBar().showMessage("Erreur: " + str(e))


def main():
    app = QApplication(sys.argv)

    # Définir l'icône de l'application
    app_icon = QIcon("assets/logo.ico")
    app.setWindowIcon(app_icon)

    window = GithubIssueGeneratorGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
