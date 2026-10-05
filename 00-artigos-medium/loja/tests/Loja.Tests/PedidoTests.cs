using Loja.Domain;
using Xunit;

namespace Loja.Tests;

public class PedidoTests
{
    [Fact]
    public void Total_PedidoNovo_RetornaZero()
    {
        var pedido = new Pedido();
        Assert.Equal(0m, pedido.Total());
    }
}