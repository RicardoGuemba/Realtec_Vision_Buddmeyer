# -*- coding: utf-8 -*-
"""
Diálogo de ajustes da câmera GenTL (Omron Sentech): gain, exposição, auto.
"""

from typing import Optional, Any, Dict

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QDoubleSpinBox, QComboBox, QFormLayout, QMessageBox,
)
from PySide6.QtCore import Qt

from core.logger import get_logger

logger = get_logger("ui.gentl_settings")


class GenTLCameraSettingsDialog(QDialog):
    """
    Tela de configurações da câmera GenTL (gain, exposição, auto exposure/auto gain).
    Requer o adaptador GenTL com stream ativo (conexão aberta).
    """

    def __init__(self, adapter: Any, parent=None):
        super().__init__(parent)
        self._adapter = adapter
        self._logger = logger
        self.setWindowTitle("Ajustes da câmera GenTL (Omron Sentech)")
        self.setMinimumWidth(420)
        self._setup_ui()
        self._refresh_from_camera()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Grupo Exposição
        exp_group = QGroupBox("Exposição")
        exp_layout = QFormLayout()
        self._exposure_spin = QDoubleSpinBox()
        self._exposure_spin.setRange(0, 1e7)
        self._exposure_spin.setDecimals(0)
        self._exposure_spin.setSuffix(" µs")
        self._exposure_spin.setToolTip("Tempo de exposição em microssegundos")
        exp_layout.addRow("Tempo (µs):", self._exposure_spin)

        self._exposure_auto_combo = QComboBox()
        self._exposure_auto_combo.setToolTip("Exposição automática")
        exp_layout.addRow("Auto:", self._exposure_auto_combo)
        layout.addWidget(exp_group)
        exp_group.setLayout(exp_layout)

        # Grupo Ganho
        gain_group = QGroupBox("Ganho")
        gain_layout = QFormLayout()
        self._gain_spin = QDoubleSpinBox()
        self._gain_spin.setRange(0, 100)
        self._gain_spin.setDecimals(2)
        self._gain_spin.setToolTip("Ganho (ex.: 0–22 dB para algumas câmeras)")
        gain_layout.addRow("Ganho:", self._gain_spin)

        self._gain_auto_combo = QComboBox()
        self._gain_auto_combo.setToolTip("Ganho automático")
        gain_layout.addRow("Auto:", self._gain_auto_combo)
        layout.addWidget(gain_group)
        gain_group.setLayout(gain_layout)

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._refresh_btn = QPushButton("Atualizar da câmera")
        self._refresh_btn.clicked.connect(self._refresh_from_camera)
        btn_layout.addWidget(self._refresh_btn)
        self._apply_btn = QPushButton("Aplicar")
        self._apply_btn.clicked.connect(self._apply_to_camera)
        btn_layout.addWidget(self._apply_btn)
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        # Guardar nomes dos nós usados (podem variar entre câmeras)
        self._exposure_node = None   # "ExposureTimeAbs" ou "ExposureTime"
        self._gain_node = "Gain"

    def _refresh_from_camera(self) -> None:
        """Lê valores atuais da câmera e preenche os controles."""
        if self._adapter is None:
            return
        features = self._adapter.get_gentl_features()
        if not features:
            self._logger.warning("gentl_settings_no_features")
            return

        # Exposição: preferir ExposureTimeAbs (µs), senão ExposureTime
        for node_name in ("ExposureTimeAbs", "ExposureTime"):
            if node_name in features:
                self._exposure_node = node_name
                info = features[node_name]
                v, mn, mx = info["value"], info["min"], info["max"]
                self._exposure_spin.setRange(mn, mx)
                self._exposure_spin.setValue(v)
                self._exposure_spin.setEnabled(info.get("writable", True))
                break
        else:
            self._exposure_spin.setEnabled(False)

        # ExposureAuto
        if "ExposureAuto" in features:
            info = features["ExposureAuto"]
            self._exposure_auto_combo.clear()
            symbolics = info.get("symbolics") or []
            if symbolics:
                self._exposure_auto_combo.addItems([str(s) for s in symbolics])
            else:
                self._exposure_auto_combo.addItems(["Off", "Once", "Continuous"])
            cur = info.get("value", "Off")
            idx = self._exposure_auto_combo.findText(str(cur))
            if idx >= 0:
                self._exposure_auto_combo.setCurrentIndex(idx)
            self._exposure_auto_combo.setEnabled(info.get("writable", True))
        else:
            self._exposure_auto_combo.setEnabled(False)

        # Gain
        if "Gain" in features:
            info = features["Gain"]
            v, mn, mx = info["value"], info["min"], info["max"]
            self._gain_spin.setRange(mn, mx)
            self._gain_spin.setValue(v)
            self._gain_spin.setEnabled(info.get("writable", True))
        else:
            self._gain_spin.setEnabled(False)

        # GainAuto
        if "GainAuto" in features:
            info = features["GainAuto"]
            self._gain_auto_combo.clear()
            symbolics = info.get("symbolics") or []
            if symbolics:
                self._gain_auto_combo.addItems([str(s) for s in symbolics])
            else:
                self._gain_auto_combo.addItems(["Off", "Once", "Continuous"])
            cur = info.get("value", "Off")
            idx = self._gain_auto_combo.findText(str(cur))
            if idx >= 0:
                self._gain_auto_combo.setCurrentIndex(idx)
            self._gain_auto_combo.setEnabled(info.get("writable", True))
        else:
            self._gain_auto_combo.setEnabled(False)

    def _apply_to_camera(self) -> None:
        """Aplica os valores atuais dos controles para a câmera."""
        if self._adapter is None:
            return
        ok_count = 0
        if self._exposure_node and self._exposure_spin.isEnabled():
            if self._adapter.set_gentl_feature(self._exposure_node, self._exposure_spin.value()):
                ok_count += 1
        if self._gain_spin.isEnabled():
            if self._adapter.set_gentl_feature("Gain", self._gain_spin.value()):
                ok_count += 1
        if self._exposure_auto_combo.isEnabled():
            val = self._exposure_auto_combo.currentText()
            if self._adapter.set_gentl_feature("ExposureAuto", val):
                ok_count += 1
        if self._gain_auto_combo.isEnabled():
            val = self._gain_auto_combo.currentText()
            if self._adapter.set_gentl_feature("GainAuto", val):
                ok_count += 1
        if ok_count > 0:
            self._logger.info("gentl_settings_applied", count=ok_count)
            QMessageBox.information(
                self,
                "Ajustes aplicados",
                "Parâmetros enviados à câmera.",
            )
        else:
            QMessageBox.warning(
                self,
                "Aviso",
                "Nenhum parâmetro pôde ser aplicado. Verifique se a câmera suporta os ajustes.",
            )
