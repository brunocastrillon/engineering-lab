using System;
using NetArchTest.Rules;
using Xunit;

public class ArchitectureTests
{
    private static readonly System.Reflection.Assembly Domain =
        typeof(Loja.Domain.Pedido).Assembly;

    [Fact]
    public void Domain_nao_depende_de_camadas_externas()
    {
        var result = Types.InAssembly(Domain)
            .ShouldNot()
            .HaveDependencyOnAny("Loja.Application", "Loja.Infrastructure", "Loja.Api")
            .GetResult();

        Assert.True(result.IsSuccessful,
            "Domain não pode depender de Application/Infrastructure/Api. " +
            "Defina uma interface em Domain e implemente em Infrastructure. " +
            "Violações: " + string.Join(", ", result.FailingTypeNames ?? Array.Empty<string>()));
    }
}