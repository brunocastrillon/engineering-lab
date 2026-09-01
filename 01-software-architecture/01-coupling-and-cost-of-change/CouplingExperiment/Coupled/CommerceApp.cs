using Coupled.Notifications;
using Coupled.Shared;

namespace Coupled
{
    /// <summary>
    /// Composition root. Every dependency is a concrete type, wired top-down in one place.
    /// </summary>
    public sealed class CommerceApp
    {
        public CommerceApp()
        {
            Store = CommerceStore.Seeded();
            Transport = new SmtpTransport();

            NotificationService notifications = new(Transport);

        }

        public CommerceStore Store { get; }
        public SmtpTransport Transport { get; }
    }
}