# Arquitetura

Direção de dependência:

    Domain  ←  Application  ←  Infrastructure  ←  Api

- **Domain**: entidades e regras de negócio. Não depende de nenhuma outra camada.
- **Application**: casos de uso. Depende só de Domain.
- **Infrastructure**: EF Core, integrações. Implementa interfaces definidas em Domain/Application.
- **Api**: controllers/endpoints e composição (DI).

Regra prática: precisa de algo de uma camada externa? Defina uma interface na camada interna
e implemente-a na externa. Estas regras são verificadas por `tests/Loja.ArchitectureTests`.
