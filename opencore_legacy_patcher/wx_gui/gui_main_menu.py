"""
gui_main_menu.py: Generate GUI for main menu
"""

import wx
import wx.html2

import sys
import logging
import requests
import markdown2
import threading
import webbrowser
from packaging import version

from .. import constants

from ..support import (
    global_settings,
    updates
)
from ..datasets import (
    os_data,
    css_data
)
from ..wx_gui import (
    gui_build,
    gui_macos_installer_download,
    gui_support,
    gui_help,
    gui_settings,
    gui_sys_patch_display,
    gui_update,
)


class _RoundedButton(wx.Panel):
    """
    Custom owner-drawn button with rounded corners and a subtle accent underline.
    Supports hover highlight and click feedback.
    Uses EVT_SIZE to always paint at the correct size.
    """
    def __init__(self, parent, label: str, bg, fg, accent,
                 size=(215, 36), handler=None, radius=10):
        super().__init__(parent, size=size, style=wx.NO_BORDER | wx.TRANSPARENT_WINDOW)
        self._label   = label
        self._bg      = bg
        self._fg      = fg
        self._accent  = accent
        self._radius  = radius
        self._hover   = False
        self._pressed = False
        self._handler = handler

        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetMinSize(size)

        self.Bind(wx.EVT_PAINT,        self._on_paint)
        self.Bind(wx.EVT_SIZE,         lambda e: self.Refresh())
        self.Bind(wx.EVT_ENTER_WINDOW, self._on_enter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._on_leave)
        self.Bind(wx.EVT_LEFT_DOWN,    self._on_down)
        self.Bind(wx.EVT_LEFT_UP,      self._on_up)

    def _on_paint(self, _evt):
        dc = wx.AutoBufferedPaintDC(self)
        w, h = self.GetClientSize()
        if w < 4 or h < 4:
            return

        # Background — match parent so transparency works
        dc.SetBackground(wx.Brush(self.GetParent().GetBackgroundColour()))
        dc.Clear()

        r = self._radius

        if self._pressed:
            fill = self._lighten(self._bg, 30)
        elif self._hover:
            fill = self._lighten(self._bg, 15)
        else:
            fill = self._bg

        gc = wx.GraphicsContext.Create(dc)
        if not gc:
            # Fallback: plain rect
            dc.SetBrush(wx.Brush(fill))
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.DrawRectangle(0, 0, w, h)
        else:
            gc.SetBrush(gc.CreateBrush(wx.Brush(fill)))
            gc.SetPen(gc.CreatePen(wx.Pen(wx.Colour(0, 0, 0, 0), 0)))
            gc.DrawRoundedRectangle(0, 0, w, h, r)

            # Accent bottom strip (3 px)
            gc.SetBrush(gc.CreateBrush(wx.Brush(self._accent)))
            gc.DrawRoundedRectangle(r, h - 3, w - r * 2, 3, 0)

        # Label text
        dc.SetFont(gui_support.font_factory(12, wx.FONTWEIGHT_BOLD))
        dc.SetTextForeground(self._fg)
        tw, th = dc.GetTextExtent(self._label)
        dc.DrawText(self._label, (w - tw) // 2, (h - th) // 2)

    @staticmethod
    def _lighten(colour: wx.Colour, amount: int) -> wx.Colour:
        return wx.Colour(
            min(255, colour.Red()   + amount),
            min(255, colour.Green() + amount),
            min(255, colour.Blue()  + amount),
        )

    def _on_enter(self, _evt): self._hover   = True;  self.Refresh()
    def _on_leave(self, _evt): self._hover   = False; self._pressed = False; self.Refresh()
    def _on_down(self,  _evt): self._pressed = True;  self.Refresh()
    def _on_up(self, evt):
        self._pressed = False
        self.Refresh()
        if self._handler:
            self._handler(evt)


class MainFrame(wx.Frame):
    def __init__(self, parent: wx.Frame, title: str, global_constants: constants.Constants, screen_location: tuple = None):
        logging.info("Initializing Main Menu Frame")
        super(MainFrame, self).__init__(parent, title=title, size=(700, 800), style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))
        gui_support.GenerateMenubar(self, global_constants).generate()

        self.constants: constants.Constants = global_constants
        self.title: str = title

        self.model_label: wx.StaticText = None
        self.build_button: wx.Button = None

        self.constants.update_stage = gui_support.AutoUpdateStages.INACTIVE

        self._generate_elements()

        self.Centre()
        self.Show()


        self._preflight_checks()


    def _generate_elements(self) -> None:
        """
        Generate UI elements — modern macOS dark-mode style.
        """
        # ── Palette ───────────────────────────────────────────────────
        BG          = wx.Colour(20,  20,  22)    # near-black window bg
        HEADER_BG   = wx.Colour(28,  28,  32)    # slightly lighter header
        CARD_BG     = wx.Colour(36,  36,  40)    # card surface
        CARD_HOVER  = wx.Colour(48,  48,  54)    # card hover (unused but defined)
        CARD_BORDER = wx.Colour(55,  55,  62)    # card outline
        BTN_BG      = wx.Colour(58,  58,  66)    # button fill
        BTN_FG      = wx.Colour(235, 235, 240)   # button text
        WHITE       = wx.Colour(255, 255, 255)
        SUBTEXT     = wx.Colour(155, 155, 162)
        ACCENT      = wx.Colour( 64, 156, 255)   # blue
        GOLD        = wx.Colour(255, 196,  64)   # nightly / spoof badge
        FOOTER_BG   = wx.Colour(26,  26,  30)

        self.SetBackgroundColour(BG)

        root = wx.BoxSizer(wx.VERTICAL)

        # ══════════════════════════════════════════════════════════════
        # HEADER PANEL
        # ══════════════════════════════════════════════════════════════
        hdr = wx.Panel(self)
        hdr.SetBackgroundColour(HEADER_BG)
        hdr_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Logo 80×80 with drop-shadow illusion via a slightly larger panel
        logo_bmp = wx.Bitmap(
            str(self.constants.icns_resource_path / "OC-Patcher.icns"),
            wx.BITMAP_TYPE_ICON
        )
        logo_img = logo_bmp.ConvertToImage().Rescale(80, 80, wx.IMAGE_QUALITY_HIGH)
        logo = wx.StaticBitmap(hdr, bitmap=wx.Bitmap(logo_img))
        hdr_sizer.Add(logo, flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=22)

        # Text column
        txt = wx.BoxSizer(wx.VERTICAL)

        app_name = wx.StaticText(hdr, label="OpenCore Legacy Patcher")
        app_name.SetFont(gui_support.font_factory(24, wx.FONTWEIGHT_BOLD))
        app_name.SetForegroundColour(WHITE)

        tagline = wx.StaticText(hdr, label="Supports Macs with T2 Chip  ·  Insider Preview")
        tagline.SetFont(gui_support.font_factory(12, wx.FONTWEIGHT_NORMAL))
        tagline.SetForegroundColour(ACCENT)

        # Version badge row
        ver_row = wx.BoxSizer(wx.HORIZONTAL)
        ver_str = f"Version {self.constants.patcher_version}"
        is_nightly = not self.constants.commit_info[0].startswith("refs/tags")
        ver_lbl = wx.StaticText(hdr, label=ver_str)
        ver_lbl.SetFont(gui_support.font_factory(11, wx.FONTWEIGHT_NORMAL))
        ver_lbl.SetForegroundColour(SUBTEXT)
        ver_row.Add(ver_lbl, flag=wx.ALIGN_CENTER_VERTICAL)
        if is_nightly:
            badge = wx.StaticText(hdr, label=" NIGHTLY ")
            badge.SetFont(gui_support.font_factory(9, wx.FONTWEIGHT_BOLD))
            badge.SetForegroundColour(GOLD)
            badge.SetBackgroundColour(wx.Colour(60, 45, 10))
            ver_row.Add(badge, flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=6)

        model_lbl = wx.StaticText(
            hdr,
            label=f"Model: {self.constants.custom_model or self.constants.computer.real_model}"
        )
        model_lbl.SetFont(gui_support.font_factory(11, wx.FONTWEIGHT_NORMAL))
        model_lbl.SetForegroundColour(SUBTEXT)
        self.model_label = model_lbl

        spoof_str = self._get_spoofed_model_label()
        spoof_lbl = wx.StaticText(hdr, label=spoof_str)
        spoof_lbl.SetFont(gui_support.font_factory(11, wx.FONTWEIGHT_BOLD))
        spoof_lbl.SetForegroundColour(
            GOLD if "None" not in spoof_str else wx.Colour(90, 90, 96)
        )
        self.spoof_label = spoof_lbl

        # Security chip label
        chip_str, chip_colour = self._get_chip_label()
        chip_lbl = wx.StaticText(hdr, label=chip_str)
        chip_lbl.SetFont(gui_support.font_factory(11, wx.FONTWEIGHT_BOLD))
        chip_lbl.SetForegroundColour(chip_colour)

        txt.Add(app_name,  flag=wx.BOTTOM, border=2)
        txt.Add(tagline,   flag=wx.BOTTOM, border=8)
        txt.Add(ver_row,   flag=wx.BOTTOM, border=3)
        txt.Add(model_lbl, flag=wx.BOTTOM, border=2)
        txt.Add(spoof_lbl, flag=wx.BOTTOM, border=2)
        txt.Add(chip_lbl)

        hdr_sizer.Add(txt, proportion=1,
                      flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, border=20)
        hdr.SetSizer(hdr_sizer)
        hdr.SetMinSize((-1, 140))

        root.Add(hdr, flag=wx.EXPAND)

        # thin accent line under header
        accent_line = wx.Panel(self, size=(-1, 2))
        accent_line.SetBackgroundColour(ACCENT)
        root.Add(accent_line, flag=wx.EXPAND)

        # ══════════════════════════════════════════════════════════════
        # FEATURE CARDS
        # ══════════════════════════════════════════════════════════════
        features = [
            {
                "label":  "Build and Install OpenCore",
                "fn":     self.on_build_and_install,
                "desc":   "Prepare a drive to boot unsupported macOS.\nUse on USB installers or internal drives.",
                "icon":   "OC-Build.icns",
                "accent": wx.Colour( 64, 156, 255),   # blue
            },
            {
                "label":  "Create macOS Installer",
                "fn":     self.on_create_macos_installer,
                "desc":   "Download and flash a macOS Installer\nfor your system.",
                "icon":   "OC-Installer.icns",
                "accent": wx.Colour( 52, 199, 120),   # green
            },
            {
                "label":  "Post-Install Root Patch",
                "fn":     self.on_post_install_root_patch,
                "desc":   "Install hardware drivers and patches\nafter a new macOS installation.",
                "icon":   "OC-Patch.icns",
                "accent": wx.Colour(255, 149,   0),   # orange
            },
            {
                "label":  "Support",
                "fn":     self.on_help,
                "desc":   "Documentation and resources for\nOpenCore Legacy Patcher.",
                "icon":   "OC-Support.icns",
                "accent": wx.Colour(175,  82, 222),   # purple
            },
        ]

        cards_panel = wx.Panel(self)
        cards_panel.SetBackgroundColour(BG)
        cards_sizer = wx.BoxSizer(wx.VERTICAL)

        for cfg in features:
            card = wx.Panel(cards_panel)
            card.SetBackgroundColour(CARD_BG)

            # left colour strip (3 px)
            strip = wx.Panel(card, size=(4, -1))
            strip.SetBackgroundColour(cfg["accent"])

            inner = wx.BoxSizer(wx.HORIZONTAL)

            # Icon 46×46
            ic_bmp = wx.Bitmap(
                str(self.constants.icns_resource_path / cfg["icon"]),
                wx.BITMAP_TYPE_ICON
            )
            ic_img = ic_bmp.ConvertToImage().Rescale(46, 46, wx.IMAGE_QUALITY_HIGH)
            ic = wx.StaticBitmap(card, bitmap=wx.Bitmap(ic_img))
            inner.Add(ic, flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, border=14)

            # Rounded button via custom-drawn panel
            btn = _RoundedButton(
                card,
                label=cfg["label"],
                bg=BTN_BG,
                fg=BTN_FG,
                accent=cfg["accent"],
                size=(215, 36),
                handler=lambda evt, f=cfg["fn"]: f(evt),
            )
            inner.Add(btn, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=16)

            # Description
            desc = wx.StaticText(card, label=cfg["desc"])
            desc.SetFont(gui_support.font_factory(10, wx.FONTWEIGHT_NORMAL))
            desc.SetForegroundColour(SUBTEXT)
            inner.Add(desc, proportion=1,
                      flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=16)

            # Assemble card: strip | inner content
            card_row = wx.BoxSizer(wx.HORIZONTAL)
            card_row.Add(strip, flag=wx.EXPAND)
            card_row.Add(inner, proportion=1, flag=wx.EXPAND | wx.TOP | wx.BOTTOM, border=10)
            card.SetSizer(card_row)
            card.SetMinSize((-1, 72))

            cards_sizer.Add(card, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=12)

        cards_panel.SetSizer(cards_sizer)
        root.Add(cards_panel, flag=wx.EXPAND | wx.BOTTOM, border=8)

        # ══════════════════════════════════════════════════════════════
        # FOOTER
        # ══════════════════════════════════════════════════════════════
        footer = wx.Panel(self)
        footer.SetBackgroundColour(FOOTER_BG)
        ft_sizer = wx.BoxSizer(wx.HORIZONTAL)

        def _footer_btn(parent, label, handler, w=124):
            b = _RoundedButton(
                parent,
                label=label,
                bg=wx.Colour(50, 50, 58),
                fg=wx.Colour(210, 210, 215),
                accent=wx.Colour(80, 80, 92),
                size=(w, 30),
                handler=handler,
                radius=8,
            )
            return b

        s_btn = _footer_btn(footer, "⚙  Settings",    self.on_settings)
        g_btn = _footer_btn(footer, "✨  Ask Gemini",  self.on_gemini_help, w=144)

        copy = wx.StaticText(footer, label=self.constants.copyright_date)
        copy.SetFont(gui_support.font_factory(9, wx.FONTWEIGHT_NORMAL))
        copy.SetForegroundColour(wx.Colour(80, 80, 88))

        ft_sizer.Add(s_btn, flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, border=8)
        ft_sizer.Add(g_btn, flag=wx.ALIGN_CENTER_VERTICAL)
        ft_sizer.AddStretchSpacer()
        ft_sizer.Add(copy,  flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=14)

        footer.SetSizer(ft_sizer)
        footer.SetMinSize((-1, 46))
        root.Add(footer, flag=wx.EXPAND)

        # ── Finalise ──────────────────────────────────────────────────
        self.SetSizer(root)
        self.SetMinSize((620, 520))
        root.Fit(self)
        self.Centre()
        self.Show()

    def _get_spoofed_model_label(self) -> str:
        """
        Return a human-readable string describing the current SMBIOS spoof target.
        Mirrors the logic in efi_builder/smbios.py without triggering a full build.
        """
        from ..support import generate_smbios

        real_model = self.constants.custom_model or self.constants.computer.real_model

        # No serial → no spoofing
        if self.constants.serial_settings == "None":
            return "Spoofing: None (Native)"

        # User picked a specific override
        if self.constants.override_smbios != "Default":
            return f"Spoofing: {self.constants.override_smbios}"

        # Native spoof allowed → stays as real model
        if self.constants.allow_native_spoofs:
            return f"Spoofing: {real_model} (Native)"

        # Compute the automatic spoof target
        try:
            target = generate_smbios.set_smbios_model_spoof(real_model)
            return f"Spoofing: {target}"
        except Exception:
            return "Spoofing: Unknown"

    def _get_chip_label(self) -> tuple:
        """
        Detect the security chip in the current Mac and return
        a (label_string, colour) tuple for display in the header.

        Detection logic:
        - T2: model is in model_array.T2Macs
        - T1: computer.t1_chip is True (detected via USB device probe)
        - None: neither T1 nor T2
        """
        from ..datasets import model_array

        real_model = self.constants.custom_model or self.constants.computer.real_model

        if real_model in model_array.T2Macs:
            return ("Chip: Apple T2 Security Chip", wx.Colour(100, 210, 255))   # cyan-blue

        if getattr(self.constants.computer, "t1_chip", False):
            return ("Chip: Apple T1 Security Chip", wx.Colour(120, 220, 140))   # green

        return ("Chip: No T1 / T2 Security Chip", wx.Colour(110, 110, 118))     # grey

    def _preflight_checks(self):
        try:
            # 1. HEAL THE CONFIG: If no build model is set, set it to the current Mac
            if self.constants.computer.build_model is None:
                logging.info("No build model detected. Defaulting to current host hardware.")
                self.constants.computer.build_model = self.constants.computer.real_model
            # Clean strings and diagnostic print
            real_model = str(self.constants.computer.real_model).strip()
            build_model = str(self.constants.computer.build_model).strip() if self.constants.computer.build_model else None
            
            print(f"DEBUG: Real: '{real_model}' | Build: '{build_model}'")

            if (
                build_model is not None and
                build_model != real_model and
                self.constants.computer.build_model != self.constants.computer.real_model and
                self.constants.host_is_hackintosh is False
            ):
                # This block is skipped for native Macs
                pop_up = wx.MessageDialog(
                    self,
                    f"We found you are currently booting OpenCore built for a different unit: {build_model}\n\nPlease Build and Install a new OpenCore config.",
                    "Unsupported Configuration Detected!",
                    style=wx.OK | wx.ICON_EXCLAMATION
                )
                pop_up.ShowModal()
                self.on_build_and_install()
                return

        except Exception as e:
            print(f"DEBUG: Preflight error: {e}")

        # The update check remains outside the if-statement
        threading.Thread(target=self._check_for_updates).start()

        if "--update_installed" in sys.argv and self.constants.has_checked_updates is False and gui_support.CheckProperties(self.constants).host_can_build():
            # Notify user that the update has been installed
            self.constants.has_checked_updates = True
            pop_up = wx.MessageDialog(
                self,
                f"OpenCore Legacy Patcher has been updated to the latest version: {self.constants.patcher_version}\n\nWould you like to update OpenCore and your root volume patches?",
                "Update successful!",
                style=wx.YES_NO | wx.YES_DEFAULT | wx.ICON_INFORMATION
            )
            pop_up.ShowModal()

            if pop_up.GetReturnCode() != wx.ID_YES:
                logging.info("Skipping OpenCore and root volume patch update...")
                return


            logging.info("Updating OpenCore and root volume patches...")
            self.constants.update_stage = gui_support.AutoUpdateStages.CHECKING
            self.Hide()
            pos = self.GetPosition()
            gui_build.BuildFrame(
                parent=None,
                title=self.title,
                global_constants=self.constants,
                screen_location=pos
            )
            self.Close()

        threading.Thread(target=self._check_for_updates).start()


    def _check_for_updates(self):
        if self.constants.has_checked_updates is True:
            return
    
        ignore_updates = global_settings.GlobalEnviromentSettings().read_property("IgnoreAppUpdates")
        if ignore_updates is True:
            self.constants.ignore_updates = True
            return
    
        self.constants.ignore_updates = False
        self.constants.has_checked_updates = True
        
        # 1. Fetch update info
        update_dict = updates.CheckBinaryUpdates(self.constants).check_binary_updates()
        if not update_dict:
            return
    
        remote_version_str = update_dict["Version"]
        local_version_str = self.constants.patcher_version
    
        try:
            # 2. Robust Comparison
            remote_v = version.parse(str(remote_version_str))
            local_v = version.parse(local_version_str)
    
            # Only trigger if remote is NEWER. 
            # If remote <= local, we are already up to date or ahead.
            if remote_v <= local_v:
                logging.info(f"OCLP-T2 is up to date. (Local: {local_v} >= Remote: {remote_v})")
                return
    
        except version.InvalidVersion:
            # Fallback for non-standard strings: only prompt if they are not identical
            if remote_version_str == local_version_str:
                return
    
        # 3. Trigger update
        logging.info(f"Newer version detected: {remote_version_str}")
        wx.CallAfter(self.on_update, update_dict["Link"], remote_version_str, update_dict["Github Link"])
        
    def on_build_and_install(self, event: wx.Event = None):
        self.Hide()
        gui_build.BuildFrame(
            parent=None,
            title=self.title,
            global_constants=self.constants,
            screen_location=self.GetPosition()
        )
        self.Destroy()


    def on_post_install_root_patch(self, event: wx.Event = None):
        gui_sys_patch_display.SysPatchDisplayFrame(
            parent=self,
            title=self.title,
            global_constants=self.constants,
            screen_location=self.GetPosition()
        )


    def on_create_macos_installer(self, event: wx.Event = None):
        gui_macos_installer_download.macOSInstallerDownloadFrame(
            parent=self,
            title=self.title,
            global_constants=self.constants,
            screen_location=self.GetPosition()
        )


    def on_settings(self, event: wx.Event = None):
        gui_settings.SettingsFrame(
            parent=self,
            title=self.title,
            global_constants=self.constants,
            screen_location=self.GetPosition()
        )

    def on_help(self, event: wx.Event = None):
        gui_help.HelpFrame(
            parent=self,
            title=self.title,
            global_constants=self.constants,
            screen_location=self.GetPosition()
        )

    def on_update(self, oclp_url: str, oclp_version: str, oclp_github_url: str):

        ID_GITHUB = wx.NewId()
        ID_UPDATE = wx.NewId()

        url = "https://api.github.com/repos/albert-mueller/OpenCore-Legacy-Patcher-T2/releases/latest"
        response = requests.get(url).json()
        try:
            changelog = response["body"].split("## Asset Information")[0]
        except: #if user constantly checks for updates, github will rate limit them
            changelog = """## Unable to fetch changelog

Please check the Github page for more information about this release."""

        html_markdown = markdown2.markdown(changelog, extras=["tables"])
        html_css = css_data.updater_css
        frame = wx.Dialog(None, -1, title="", size=(650, 500))
        frame.SetMinSize((650, 500))
        frame.SetWindowStyle(wx.STAY_ON_TOP)
        panel = wx.Panel(frame)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(10)
        self.title_text = wx.StaticText(panel, label="A new version of OpenCore Legacy Patcher T2 is available!")
        self.description = wx.StaticText(panel, label=f"OpenCore Legacy Patcher T2 {oclp_version} is now available - You have {self.constants.patcher_version}{' (Nightly)' if not self.constants.commit_info[0].startswith('refs/tags') else ''}. Would you like to update?")
        self.title_text.SetFont(gui_support.font_factory(19, wx.FONTWEIGHT_BOLD))
        self.description.SetFont(gui_support.font_factory(13, wx.FONTWEIGHT_NORMAL))
        self.web_view = wx.html2.WebView.New(panel, style=wx.BORDER_SUNKEN)
        html_code = f'''
<html>
    <head>
        <style>
            {html_css}
        </style>
    </head>
    <body class="markdown-body">
        {html_markdown.replace("<a href=", "<a target='_blank' href=")}
    </body>
</html>
'''
        self.web_view.SetPage(html_code, "")
        self.web_view.Bind(wx.html2.EVT_WEBVIEW_NEWWINDOW, self._onWebviewNav)
        self.web_view.EnableContextMenu(False)
        self.close_button = wx.Button(panel, label="Dismiss")
        self.close_button.Bind(wx.EVT_BUTTON, lambda event: frame.EndModal(wx.ID_CANCEL))
        self.view_button = wx.Button(panel, ID_GITHUB, label="View on GitHub")
        self.view_button.Bind(wx.EVT_BUTTON, lambda event: frame.EndModal(ID_GITHUB))
        self.install_button = wx.Button(panel, label="Download and Install")
        self.install_button.Bind(wx.EVT_BUTTON, lambda event: frame.EndModal(ID_UPDATE))
        self.install_button.SetDefault()

        buttonsizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonsizer.Add(self.close_button, 0, wx.ALIGN_CENTRE | wx.RIGHT, 5)
        buttonsizer.Add(self.view_button, 0, wx.ALIGN_CENTRE | wx.LEFT|wx.RIGHT, 5)
        buttonsizer.Add(self.install_button, 0, wx.ALIGN_CENTRE | wx.LEFT, 5)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.title_text, 0, wx.ALIGN_CENTRE | wx.TOP, 20)
        sizer.Add(self.description, 0, wx.ALIGN_CENTRE | wx.BOTTOM, 20)
        sizer.Add(self.web_view, 1, wx.EXPAND | wx.LEFT|wx.RIGHT, 10)
        sizer.Add(buttonsizer, 0, wx.ALIGN_RIGHT | wx.ALL, 20)
        panel.SetSizer(sizer)
        frame.Centre()

        result = frame.ShowModal()


        if result == ID_GITHUB:
            webbrowser.open(oclp_github_url)
        elif result == ID_UPDATE:
            gui_update.UpdateFrame(
            parent=self,
            title=self.title,
            global_constants=self.constants,
            screen_location=self.GetPosition(),
            url=oclp_url,
            version_label=oclp_version
        )

        frame.Destroy()

    def _onWebviewNav(self, event):
        url = event.GetURL()
        webbrowser.open(url)
    
    def on_gemini_help(self, event: wx.Event):
        import webbrowser
        logging.info("- Launching Gemini AI Assistant in default browser")
        webbrowser.open('https://gemini.google.com')
