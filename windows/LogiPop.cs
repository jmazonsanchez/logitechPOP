using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Windows.Forms;
using System.Drawing;

namespace LogiPop
{
    static class Program
    {
        [STAThread]
        static void Main()
        {
            // Evitar múltiples instancias
            bool createdNew;
            using (var mutex = new System.Threading.Mutex(true, "LogiPop_Sync_Mutex", out createdNew))
            {
                if (!createdNew) return;

                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                Application.Run(new LogiPopContext());
            }
        }
    }

    public class LogiPopContext : ApplicationContext
    {
        private NotifyIcon trayIcon;
        private MessageWindow msgWindow;

        public LogiPopContext()
        {
            msgWindow = new MessageWindow(this);
            trayIcon = new NotifyIcon()
            {
                Icon = SystemIcons.Application,
                Text = "LogiPop Sync (Win+Alt+1/2/3)",
                Visible = true
            };

            ContextMenu menu = new ContextMenu();
            menu.MenuItems.Add("LogiPop Sync (Activo)").Enabled = false;
            menu.MenuItems.Add("-");
            menu.MenuItems.Add("Salir", (s, e) => {
                trayIcon.Visible = false;
                Application.Exit();
            });
            trayIcon.ContextMenu = menu;

            trayIcon.ShowBalloonTip(2000, "LogiPop Sync", "Atajos Win+Alt+1/2/3 activos para conmutación rápida.", ToolTipIcon.Info);
        }

        public void Notify(string text)
        {
            if (trayIcon != null)
            {
                trayIcon.ShowBalloonTip(1500, "LogiPop Sync", text, ToolTipIcon.Info);
            }
        }
    }

    internal class MessageWindow : Form
    {
        private const int WM_HOTKEY = 0x0312;
        private const int MOD_ALT = 0x0001;
        private const int MOD_WIN = 0x0008;

        [DllImport("user32.dll", SetLastError = true)]
        private static extern bool RegisterHotKey(IntPtr hWnd, int id, int fsModifiers, int vk);

        [DllImport("user32.dll", SetLastError = true)]
        private static extern bool UnregisterHotKey(IntPtr hWnd, int id);

        private LogiPopContext context;

        public MessageWindow(LogiPopContext ctx)
        {
            context = ctx;
            // 0x31 = '1', 0x32 = '2', 0x33 = '3'
            RegisterHotKey(this.Handle, 1, MOD_WIN | MOD_ALT, 0x31);
            RegisterHotKey(this.Handle, 2, MOD_WIN | MOD_ALT, 0x32);
            RegisterHotKey(this.Handle, 3, MOD_WIN | MOD_ALT, 0x33);
        }

        protected override void WndProc(ref Message m)
        {
            if (m.Msg == WM_HOTKEY)
            {
                int channel = m.WParam.ToInt32();
                context.Notify("Cambiando teclado y mouse al Canal " + channel + "...");
                DeviceSwitcher.Switch(channel - 1);
            }
            base.WndProc(ref m);
        }

        protected override void Dispose(bool disposing)
        {
            UnregisterHotKey(this.Handle, 1);
            UnregisterHotKey(this.Handle, 2);
            UnregisterHotKey(this.Handle, 3);
            base.Dispose(disposing);
        }
    }

    internal static class DeviceSwitcher
    {
        [DllImport("hid.dll", SetLastError = true)]
        private static extern void HidD_GetHidGuid(out Guid hidGuid);

        [DllImport("setupapi.dll", SetLastError = true, CharSet = CharSet.Auto)]
        private static extern IntPtr SetupDiGetClassDevs(ref Guid ClassGuid, string Enumerator, IntPtr hwndParent, uint Flags);

        [DllImport("setupapi.dll", SetLastError = true)]
        private static extern bool SetupDiEnumDeviceInterfaces(IntPtr DeviceInfoSet, IntPtr DeviceInfoData, ref Guid InterfaceClassGuid, uint MemberIndex, ref SP_DEVICE_INTERFACE_DATA DeviceInterfaceData);

        [DllImport("setupapi.dll", SetLastError = true, CharSet = CharSet.Auto)]
        private static extern bool SetupDiGetDeviceInterfaceDetail(IntPtr DeviceInfoSet, ref SP_DEVICE_INTERFACE_DATA DeviceInterfaceData, IntPtr DeviceInterfaceDetailData, uint DeviceInterfaceDetailDataSize, ref uint RequiredSize, IntPtr DeviceInfoData);

        [DllImport("setupapi.dll", SetLastError = true)]
        private static extern bool SetupDiDestroyDeviceInfoList(IntPtr DeviceInfoSet);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        private static extern IntPtr CreateFile(string lpFileName, uint dwDesiredAccess, uint dwShareMode, IntPtr lpSecurityAttributes, uint dwCreationDisposition, uint dwFlagsAndAttributes, IntPtr hTemplateFile);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool WriteFile(IntPtr hFile, byte[] lpBuffer, uint nNumberOfBytesToWrite, out uint lpNumberOfBytesWritten, IntPtr lpOverlapped);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool CloseHandle(IntPtr hObject);

        [StructLayout(LayoutKind.Sequential)]
        private struct SP_DEVICE_INTERFACE_DATA
        {
            public uint cbSize;
            public Guid InterfaceClassGuid;
            public uint Flags;
            public IntPtr Reserved;
        }

        private const uint DIGCF_PRESENT = 0x00000002;
        private const uint DIGCF_DEVICEINTERFACE = 0x00000010;
        private const uint GENERIC_READ = 0x80000000;
        private const uint GENERIC_WRITE = 0x40000000;
        private const uint FILE_SHARE_READ = 0x00000001;
        private const uint FILE_SHARE_WRITE = 0x00000002;
        private const uint OPEN_EXISTING = 3;

        public static void Switch(int targetIndex)
        {
            Guid hidGuid;
            HidD_GetHidGuid(out hidGuid);

            IntPtr hDevInfo = SetupDiGetClassDevs(ref hidGuid, null, IntPtr.Zero, DIGCF_PRESENT | DIGCF_DEVICEINTERFACE);
            if (hDevInfo == IntPtr.Zero || hDevInfo.ToInt64() == -1) return;

            try
            {
                SP_DEVICE_INTERFACE_DATA dia = new SP_DEVICE_INTERFACE_DATA();
                dia.cbSize = (uint)Marshal.SizeOf(dia);

                uint index = 0;
                while (SetupDiEnumDeviceInterfaces(hDevInfo, IntPtr.Zero, ref hidGuid, index++, ref dia))
                {
                    uint requiredSize = 0;
                    SetupDiGetDeviceInterfaceDetail(hDevInfo, ref dia, IntPtr.Zero, 0, ref requiredSize, IntPtr.Zero);
                    if (requiredSize == 0) continue;

                    IntPtr detailData = Marshal.AllocHGlobal((int)requiredSize);
                    try
                    {
                        Marshal.WriteInt32(detailData, (IntPtr.Size == 8) ? 8 : 5);
                        if (SetupDiGetDeviceInterfaceDetail(hDevInfo, ref dia, detailData, requiredSize, ref requiredSize, IntPtr.Zero))
                        {
                            IntPtr pDevicePath = new IntPtr(detailData.ToInt64() + 4);
                            string path = Marshal.PtrToStringAuto(pDevicePath);
                            if (string.IsNullOrEmpty(path)) continue;

                            string pathLower = path.ToLowerInvariant();
                            if (pathLower.Contains("046d") || pathLower.Contains("vid_046d") || pathLower.Contains("vid&046d"))
                            {
                                byte[] packet = null;

                                // Logi POP Mouse (B030) - Feature 0x1814 en índice 0x0A
                                if (pathLower.Contains("b030"))
                                {
                                    packet = new byte[20];
                                    packet[0] = 0x11;
                                    packet[1] = 0xFF;
                                    packet[2] = 0x0A;
                                    packet[3] = 0x18;
                                    packet[4] = (byte)targetIndex;
                                }
                                // Logi POP Keys (B365) - Feature 0x1814 en índice 0x09
                                else if (pathLower.Contains("b365"))
                                {
                                    packet = new byte[20];
                                    packet[0] = 0x11;
                                    packet[1] = 0xFF;
                                    packet[2] = 0x09;
                                    packet[3] = 0x18;
                                    packet[4] = (byte)targetIndex;
                                }

                                if (packet != null)
                                {
                                    SendPacket(path, packet);
                                }
                            }
                        }
                    }
                    finally
                    {
                        Marshal.FreeHGlobal(detailData);
                    }
                }
            }
            finally
            {
                SetupDiDestroyDeviceInfoList(hDevInfo);
            }
        }

        private static void SendPacket(string path, byte[] packet)
        {
            IntPtr handle = CreateFile(path, GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, IntPtr.Zero, OPEN_EXISTING, 0, IntPtr.Zero);
            if (handle != IntPtr.Zero && handle.ToInt64() != -1)
            {
                try
                {
                    uint written;
                    WriteFile(handle, packet, (uint)packet.Length, out written, IntPtr.Zero);
                }
                catch { }
                finally
                {
                    CloseHandle(handle);
                }
            }
        }
    }
}
